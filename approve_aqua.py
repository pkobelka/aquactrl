#!/usr/bin/env python3
"""
AquaControl – schválení zařízení (push notifikace)
==================================================
Nastaví `schvaleno: true` u zařízení v uzlu `aqua_push_tokens`.

Použití:
    python approve_aqua.py            # schválí všechna čekající (schvaleno:false)
    python approve_aqua.py ac-xxxx    # schválí jen jedno zařízení (Device ID)

Náhrada za in-app obrazovku „Zařízení" (ta čte celý seznam tokenů, což
bezpečnostní pravidla z prohlížeče blokují). Sdílí Firebase projekt moje-budky.
"""

import sys
import firebase_admin
from firebase_admin import credentials, db

SERVICE_ACCOUNT = 'service-account-key.json'
DATABASE_URL    = 'https://moje-budky-default-rtdb.firebaseio.com'
NODE            = 'aqua_push_tokens'

# kód osoby -> celé jméno (drž v souladu s LIDE v index.html)
LIDE = {
    'AB': 'Aleš Bubák', 'BK': 'Bláža Kolaříková', 'JR': 'Jan Rada',
    'GŘ': 'Jana Drábková', 'LV': 'Lukáš Vykydal', 'MH': 'Milan Horník',
    'PŘ': 'Tomáš Zvejška', 'VH': 'Vladislav Halva', 'TŘ': 'Petr Kobelka',
    'JF': 'Jiří Fogl', 'KK': 'Karel Krombholz', 'KN': 'Kristýna Nerušilová',
    'ZS': 'Zdeněk Sojma', 'EJ': 'Eva Jančáková', 'KV': 'Kateřina Vávrová',
    'SŠ': 'Stanislav Škeřík', 'JB': 'Jiří Bombera', 'PK': 'Petra Křečková',
    'PT': 'Pavlína Tillová', 'DM': 'Dana Mikulková', 'AK': 'Alena Kobelková',
    'PKa': 'Petra Kačerová', 'KM': 'Kamil Michalčák', 'JT': 'Jiří Tinkl',
    'ZK': 'Zdeněk Krejsa',
}


def jmeno(person):
    return LIDE.get(person, person or '(bez jména)')


def main():
    target_id = sys.argv[1].strip() if len(sys.argv) > 1 else ''

    cred = credentials.Certificate(SERVICE_ACCOUNT)
    firebase_admin.initialize_app(cred, {'databaseURL': DATABASE_URL})

    snap = db.reference(NODE).get()
    if not snap:
        print('Žádná registrovaná zařízení.')
        return

    schvalena = []
    for key, val in snap.items():
        if not isinstance(val, dict):
            continue
        if target_id:
            if key != target_id:
                continue
        else:
            # bez cíle: jen ta, co čekají (schvaleno:false)
            if val.get('schvaleno') is not False:
                continue
        db.reference(f'{NODE}/{key}/schvaleno').set(True)
        schvalena.append((key, val.get('person'), (val.get('ua') or '')[:40]))

    if not schvalena:
        print(f'Nic ke schválení (cíl: "{target_id}").' if target_id
              else 'Žádná čekající zařízení – vše už je schválené.')
        return

    print(f'Schváleno {len(schvalena)} zařízení:')
    for key, person, ua in schvalena:
        print(f'  • {jmeno(person)} ({person})  ·  {ua}  ·  {key}')


if __name__ == '__main__':
    main()
