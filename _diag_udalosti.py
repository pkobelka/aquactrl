#!/usr/bin/env python3
# Jednorázová diagnostika: vypíše strukturální pole otevřených událostí
# (stredisko, kat, objekt, uzavreno) + počty po stredisko|kat.
# Žádná osobní data (popis/nahlásil/telefon) se netisknou.
import firebase_admin
from firebase_admin import credentials, db
from collections import Counter

cred = credentials.Certificate('service-account-key.json')
firebase_admin.initialize_app(cred, {'databaseURL': 'https://moje-budky-default-rtdb.firebaseio.com'})

snap = db.reference('aquactrl_udalosti').get() or {}
print(f'Celkem zaznamu v aquactrl_udalosti: {len(snap)}')
counts = Counter()
for k, e in snap.items():
    if not isinstance(e, dict):
        print(f'  {k[:8]}: NENI dict ({type(e).__name__})')
        continue
    uz = e.get('uzavreno')
    st = e.get('stredisko')
    kat = e.get('kat')
    obj = e.get('objekt')
    has_kat = 'kat' in e
    if not uz:
        counts[f'{st}|{kat}'] += 1
    print(f'  {k[:8]} uzavreno={uz!r} stredisko={st!r} kat={kat!r} has_kat={has_kat} objekt={obj!r}')
print('--- pocty OTEVRENYCH po stredisko|kat ---')
for key, c in sorted(counts.items()):
    print(f'  {key} = {c}')
