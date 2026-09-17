#!/usr/bin/env python3
"""
AquaCtrl – přihlašovací QR (pro člověka bez e-mailu)
=======================================================
Vygeneruje **jednorázový přihlašovací odkaz** (Firebase email-link sign-in) přes
Admin SDK – tedy bez toho, aby se cokoli posílalo do schránky – udělá z něj QR kód
a uloží ho do uzlu `aquactrl_qr_login`. Admin si ho pak otevře v appce
(menu „Přihlašovací QR“) a dotyčnému ho ukáže na displeji / pošle odkaz SMSkou.

Na co to je: kdo nemá e-mail (nebo se do něj na místě nedostane), naskenuje QR
a je přihlášený. Přihlášení pak drží trvale, takže tohle je jednorázová věc.

⚠️ Proč to nejde jako artefakt z GitHub Actions: repozitář je **veřejný**, takže
artefakty i logy běhů si může stáhnout kdokoli. Odkaz je plnohodnotný klíč do
appky, proto se nikam do Actions nevypisuje – jen do databáze, kterou čte pouze
admin (pravidlo `aquactrl_qr_login` v `database.rules.json`, viz SECURITY.md).

Použití:
    python login_qr_aquactrl.py <e-mail> [kod osoby]      # vygeneruje QR do appky
    python login_qr_aquactrl.py <e-mail> [kod] --minut 30 # jiná platnost (výchozí 60)
    python login_qr_aquactrl.py <e-mail> --png qr.png     # navíc uloží PNG na disk
    python login_qr_aquactrl.py <e-mail> --odkaz          # vypíše odkaz (jen lokálně!)
    python login_qr_aquactrl.py uklid                     # smaže prošlé pozvánky

Kód osoby (z LIDE) je potřeba jen tehdy, když e-mail ještě není v „Přístup
(e-maily)“ – skript ho tam rovnou doplní. Bez povoleného e-mailu by appka
dotyčného po přihlášení stejně odmítla.

Kdo nemá e-mail vůbec, dostane zástupnou adresu (třeba `jan.novak@aquactrl.local`) –
nemusí existovat, slouží jen jako jeho identita v appce.

Po prvním přihlášení dotyčného spusť ještě workflow „Nastavit identity uživatelů“
(`sync_person_claims.py`), ať dostane ověřený claim `person`.
"""

import argparse
import base64
import io
import os
import secrets
import sys
import time
from urllib.parse import quote

import firebase_admin
from firebase_admin import credentials, auth, db

SERVICE_ACCOUNT = 'service-account-key.json'
DATABASE_URL    = 'https://moje-budky-default-rtdb.firebaseio.com'
NODE            = 'aquactrl_qr_login'
NODE_EMAILY     = 'aquactrl_login_email'
LOGIN_URL       = 'https://pkobelka.github.io/aquactrl/'
VYCHOZI_MINUT   = 60


def key(email):
    """Klíč v aquactrl_login_email – malá písmena, tečky za čárky (Firebase klíč nesmí mít '.')."""
    return email.strip().lower().replace('.', ',')


def init():
    cred = credentials.Certificate(SERVICE_ACCOUNT)
    firebase_admin.initialize_app(cred, {'databaseURL': DATABASE_URL})


def uklid():
    """Smaže prošlé pozvánky (běží i před každým generováním)."""
    ref = db.reference(NODE)
    now = int(time.time() * 1000)
    smazano = 0
    for qid, rec in (ref.get() or {}).items():
        if not isinstance(rec, dict) or rec.get('platiDo', 0) < now:
            ref.child(qid).delete()
            smazano += 1
    return smazano


def qr_png(odkaz):
    """QR jako PNG v base64 (ukládá se rovnou do DB, appka ho jen zobrazí jako <img>)."""
    try:
        import qrcode
    except ImportError:
        sys.exit('Chybí knihovna qrcode – nainstaluj: pip install "qrcode[pil]"')
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=2)
    qr.add_data(odkaz)
    qr.make(fit=True)
    buf = io.BytesIO()
    qr.make_image(fill_color='black', back_color='white').save(buf, format='PNG', optimize=True)
    return buf.getvalue()


def main():
    p = argparse.ArgumentParser(description='AquaCtrl – přihlašovací QR')
    p.add_argument('email', help='e-mail dotyčného (nebo "uklid" pro smazání prošlých)')
    p.add_argument('kod', nargs='?', default='', help='kód osoby z LIDE (když e-mail ještě nemá přístup)')
    p.add_argument('--minut', type=int, default=VYCHOZI_MINUT, help=f'platnost pozvánky v minutách (výchozí {VYCHOZI_MINUT})')
    p.add_argument('--png', default='', help='uložit QR i jako PNG na disk (jen lokálně)')
    p.add_argument('--odkaz', action='store_true', help='vypsat odkaz na obrazovku (jen lokálně, NE v Actions)')
    a = p.parse_args()

    init()

    if a.email.strip().lower() == 'uklid':
        print(f'Smazáno prošlých pozvánek: {uklid()}')
        return

    # Pojistka: ve veřejném repu jsou logy běhů vidět všem, odkaz do nich nepatří.
    if a.odkaz and os.environ.get('GITHUB_ACTIONS') == 'true':
        sys.exit('--odkaz nejde použít v GitHub Actions (logy veřejného repa vidí kdokoli). '
                 'Odkaz najdeš v appce v menu „Přihlašovací QR“.')

    email = a.email.strip().lower()
    if '@' not in email:
        sys.exit(f'„{a.email}“ nevypadá jako e-mail.')
    minut = max(5, min(a.minut, 24 * 60))

    # 1) Přístup – bez záznamu v aquactrl_login_email appka dotyčného po přihlášení odmítne.
    eref = db.reference(f'{NODE_EMAILY}/{key(email)}')
    kod = (eref.get() or '')
    if a.kod.strip():
        kod = a.kod.strip()
        eref.set(kod)
        print(f'Přístup nastaven: {email} -> {kod}')
    elif not kod:
        sys.exit(f'{email} zatím nemá přístup. Zadej kód osoby z LIDE jako druhý parametr '
                 '(nebo ho přidej v appce v „Přístup (e-maily)“).')

    # 2) Jednorázový přihlašovací odkaz. E-mail dáme do `continueUrl` (?e=…), aby ho
    #    appka po naskenování znala a dotyčný ho nemusel opisovat.
    nastaveni = auth.ActionCodeSettings(
        url=f'{LOGIN_URL}?e={quote(email, safe="")}',
        handle_code_in_app=True,
    )
    odkaz = auth.generate_sign_in_with_email_link(email, action_code_settings=nastaveni)

    # 3) Ulož do DB (čte jen admin) – pro zobrazení v appce.
    smazano = uklid()
    now = int(time.time() * 1000)
    qid = secrets.token_hex(8)
    db.reference(f'{NODE}/{qid}').set({
        'email': email,
        'kod': kod,
        'odkaz': odkaz,
        'png': 'data:image/png;base64,' + base64.b64encode(qr_png(odkaz)).decode('ascii'),
        'vytvoreno': now,
        'platiDo': now + minut * 60 * 1000,
    })

    print(f'Hotovo: QR pro {email} ({kod}), platí {minut} min.')
    if smazano:
        print(f'  (uklizeno prošlých pozvánek: {smazano})')
    print('Otevři appku → menu „Přihlašovací QR“ a nech dotyčného naskenovat.')
    print('Po jeho prvním přihlášení spusť ještě workflow „Nastavit identity uživatelů“.')

    if a.png:
        with open(a.png, 'wb') as f:
            f.write(qr_png(odkaz))
        print(f'  PNG uloženo: {a.png}')
    if a.odkaz:
        print(f'\nOdkaz (jednorázový, nikam ho neukládej):\n{odkaz}')


if __name__ == '__main__':
    main()
