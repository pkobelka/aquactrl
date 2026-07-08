#!/usr/bin/env python3
"""
AquaCtrl – hlídání zmeškaných termínů úkolů
===============================================
Appka sama o sobě žádné pozadí nemá (statická stránka), takže zmeškaný
termín úkolu by jinak nikdo nezaznamenal. Tenhle skript pravidelně
(viz .github/workflows/check-terminy.yml) projde uzel `aquactrl_ukoly`,
najde nesplněné úkoly po termínu, kterým ještě nebylo posláno avízo,
a jednou (ne opakovaně) o tom pošle push lidem z pole "upozornit" –
stejnou frontou `aquactrl_outbox`, jakou používá appka (vyzvedne ji sdílená
Cloud Function a pošle FCM push).
"""

import time
import firebase_admin
from firebase_admin import credentials, db

SERVICE_ACCOUNT = 'service-account-key.json'
DATABASE_URL    = 'https://moje-budky-default-rtdb.firebaseio.com'
NODE            = 'aquactrl_ukoly'


def main():
    cred = credentials.Certificate(SERVICE_ACCOUNT)
    firebase_admin.initialize_app(cred, {'databaseURL': DATABASE_URL})

    now = int(time.time() * 1000)
    snap = db.reference(NODE).get() or {}

    poslano = 0
    for key, u in snap.items():
        if not isinstance(u, dict):
            continue
        if u.get('stav') == 'splneny':
            continue
        termin = u.get('termin')
        if not termin or termin >= now:
            continue
        if u.get('poterminu_upozorneno'):
            continue
        targets = list(u.get('upozornit') or [])
        zadal = u.get('zadal')
        if zadal and zadal not in targets:
            targets.append(zadal)  # zadavatel dostane avízo vždy (i bez vyplněného pole "upozornit")
        if not targets:
            continue

        popis = u.get('popis') or 'úkol'
        resitel = u.get('resitel_jmeno') or u.get('resitel') or '?'
        kontext = u.get('kontext') or ''
        body = f'{resitel} nesplnil/a do termínu: {popis}' + (f' – {kontext}' if kontext else '')

        db.reference('aquactrl_outbox').push({
            'title': '⏰ Úkol po termínu',
            'body': body,
            'targets': targets,
            'ts': now,
        })
        db.reference(f'{NODE}/{key}').update({
            'poterminu_upozorneno': True,
            'poterminu_upozorneno_ts': now,
        })
        poslano += 1
        print(f'  • {popis} (řešitel {resitel}) → upozorněno: {targets}')

    print(f'\nHotovo: {poslano} úkol(ů) po termínu nově nahlášeno.' if poslano
          else 'Žádné nové úkoly po termínu k nahlášení.')


if __name__ == '__main__':
    main()
