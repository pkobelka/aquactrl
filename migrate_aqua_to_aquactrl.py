#!/usr/bin/env python3
"""
AquaCtrl – migrace dat ze starých uzlů (aqua_*) do nových (aquactrl_*)
=======================================================================
Jednorázový skript k dokončení přejmenování appky z AquaControl na
AquaCtrl. Zkopíruje obsah starých Firebase uzlů do nových – stará data
NEMAŽE (zůstanou v DB jako záloha; appka po nasazení nové verze kódu
už na ně nebude sahat, čte/píše jen do aquactrl_*).

Použití:
    python migrate_aqua_to_aquactrl.py             # zkontroluje a zkopíruje vše
    python migrate_aqua_to_aquactrl.py --dry-run    # jen ukáže, co by se stalo, nic nezapíše

Bezpečnostní pojistka: pokud cílový uzel (aquactrl_*) už obsahuje data,
skript ho PŘESKOČÍ a upozorní (aby omylem nepřepsal něco, co tam už je).

Spouštět ručně, ne přes GitHub Actions – je to jednorázová operace nad
živou databází, chceš mít výsledek rovnou před očima.
"""

import sys
import firebase_admin
from firebase_admin import credentials, db

SERVICE_ACCOUNT = 'service-account-key.json'
DATABASE_URL    = 'https://moje-budky-default-rtdb.firebaseio.com'

NODES = [
    'aqua_udalosti', 'aqua_ukoly', 'aqua_outbox', 'aqua_zarizeni',
    'aqua_push_tokens', 'aqua_login_email', 'aqua_presence',
]


def main():
    dry_run = '--dry-run' in sys.argv

    cred = credentials.Certificate(SERVICE_ACCOUNT)
    firebase_admin.initialize_app(cred, {'databaseURL': DATABASE_URL})

    print('Režim: ' + ('DRY RUN (nic se nezapíše)' if dry_run else 'OSTRÝ BĚH (zapisuje do DB)'))
    print()

    for old_node in NODES:
        new_node = old_node.replace('aqua_', 'aquactrl_', 1)
        old_data = db.reference(old_node).get()

        if old_data is None:
            print(f'  {old_node:20s} -> {new_node:24s}  (prázdné, přeskočeno)')
            continue

        existing = db.reference(new_node).get()
        if existing:
            print(f'  {old_node:20s} -> {new_node:24s}  POZOR: cíl už obsahuje data, PŘESKOČENO (zkontroluj ručně)')
            continue

        count = len(old_data) if isinstance(old_data, dict) else 1
        if dry_run:
            print(f'  {old_node:20s} -> {new_node:24s}  zkopírovalo by se {count} položek')
        else:
            db.reference(new_node).set(old_data)
            print(f'  {old_node:20s} -> {new_node:24s}  zkopírováno {count} položek')

    print()
    if dry_run:
        print('Dry run hotov. Pro skutečnou migraci spusť bez --dry-run.')
    else:
        print('Hotovo. Staré uzly (aqua_*) zůstávají v DB nedotčené jako záloha.')
        print('Až si ověříš, že appka běží v pořádku, můžeš je ručně smazat ve Firebase konzoli.')


if __name__ == '__main__':
    main()
