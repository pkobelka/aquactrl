#!/usr/bin/env python3
"""
AquaControl – naplnění seznamu povolených přihlašovacích e-mailů
=================================================================
Zapíše do uzlu `aqua_login_email` mapování e-mail -> kód osoby (LIDE).
Appka podle něj po přihlášení e-mailovým odkazem pozná, kdo je přihlášený
(localStorage.ac_person), a Firebase pravidla podle něj řídí přístup k datům.

Použití:
    python seed_login_email.py                  # doplní chybějící ze seznamu EMAILY níže
    python seed_login_email.py pridej e-mail kod # přidá/aktualizuje jeden záznam

Existující záznamy (např. přidané ručně přes appku "Přístup (e-maily)")
se nepřepisují – skript jen doplňuje, co tam ještě není.
"""

import sys
import firebase_admin
from firebase_admin import credentials, db

SERVICE_ACCOUNT = 'service-account-key.json'
DATABASE_URL    = 'https://moje-budky-default-rtdb.firebaseio.com'
NODE            = 'aqua_login_email'

# kód osoby -> e-mail (drž v souladu s KONTAKTY v index.html)
# Pozn.: ZK (Zdeněk Krejsa) nemá v KONTAKTY e-mail vůbec –
# je potřeba se zeptat a přidat ho ručně (přes appku nebo "pridej").
EMAILY = {
    'GŘ': 'jana.drabkova@vhos.cz', 'PŘ': 'tomas.zvejska@vhos.cz', 'TŘ': 'petr.kobelka@vhos.cz',
    'AB': 'ales.bubak@vhos.cz', 'BK': 'blazena.kolarikova@vhos.cz', 'JR': 'jan.rada@vhos.cz',
    'LV': 'lukas.vykydal@vhos.cz', 'MH': 'hornikm@atlas.cz', 'VH': 'vladimir.halva@vhos.cz',
    'JF': 'jiri.fogl@vhos.cz', 'KK': 'karel.krombholz@vhos.cz', 'KN': 'kristyna.nerusilova@vhos.cz',
    'ZS': 'zdenek.sojma@vhos.cz', 'EJ': 'eva.jancakova@vhos.cz', 'KV': 'katerina.vavrova@vhos.cz',
    'SŠ': 'stanislav.skerik@cevak.cz', 'JB': 'jiri.bombera@cevak.cz', 'PK': 'petra.kreckova@cevak.cz',
    'PT': 'pavlina.tillova@cevak.cz', 'DM': 'dana.mikulkova@vhos.cz', 'AK': 'alena.kobelkova@vhos.cz',
    'PKa': 'petra.kacerova@vhos.cz', 'KM': 'kamil.michalcak@vhos.cz', 'ZD': 'zdenek.drabek@vhos.cz',
    'JT': 'jirkatinkl@gmail.com', 'MP': 'michalprokop26@email.cz',
}


def key(email):
    return email.strip().lower().replace('.', ',')


def main():
    cred = credentials.Certificate(SERVICE_ACCOUNT)
    firebase_admin.initialize_app(cred, {'databaseURL': DATABASE_URL})
    ref = db.reference(NODE)

    if len(sys.argv) >= 4 and sys.argv[1] == 'pridej':
        email, kod = sys.argv[2].strip(), sys.argv[3].strip()
        ref.child(key(email)).set(kod)
        print(f'Přidáno: {email} -> {kod}')
        return

    existing = ref.get() or {}
    pridano = 0
    for kod, email in EMAILY.items():
        k = key(email)
        if k in existing:
            continue
        ref.child(k).set(kod)
        pridano += 1
        print(f'  + {email} -> {kod}')

    print(f'\nHotovo: {pridano} nových záznamů (existující se nepřepisují).')
    print('Bez e-mailu v KONTAKTY zůstávají: JT (Jiří Tinkl), ZK (Zdeněk Krejsa) – doplň ručně.')


if __name__ == '__main__':
    main()
