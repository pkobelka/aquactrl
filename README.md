# AquaCtrl

PWA pro evidenci provozních (mimořádných) událostí na vodárenské infrastruktuře **VHOS a.s.** – „mimka" / klikací prototyp. Vše je v jednom souboru `index.html` (inline CSS+JS) + ikony, `manifest.json`, `sw.js`, FCM push.

- **Živá adresa:** https://pkobelka.github.io/aquactrl/
- Pozn.: stále jde o **mimku** – data se reálně neukládají (kromě push tokenů). Push notifikace fungují (sdílí Firebase projekt `moje-budky`).

## První nasazení (jednorázově)

1. **GitHub Pages:** Settings → Pages → Source = *Deploy from a branch*, Branch = `main` / `/ (root)` → Save. Za chvíli naběhne https://pkobelka.github.io/aquactrl/
2. **Push notifikace (Actions secret):** Settings → Secrets and variables → Actions → *New repository secret*
   - Name: `FIREBASE_SERVICE_ACCOUNT`
   - Value: celý obsah service-account JSON z Firebase projektu `moje-budky` (stejný, jaký je v repu `mojebudky`).
   - Bez tohoto secretu nebude fungovat workflow „Odeslat push".

Doména `pkobelka.github.io` je v Firebase už autorizovaná (stejný origin jako budky), takže **VAPID/config netřeba měnit**.

3. **Přihlašování e-mailem (Firebase Auth):** Firebase Console → Authentication → Sign-in method → povolit provider *Email/Password* a v něm zapnout přepínač *Email link (passwordless sign-in)*. Pak Authentication → Settings → Authorized domains → ověřit/přidat `pkobelka.github.io` (tohle je jiné nastavení než autorizace domény pro FCM výše, nepředpokládat, že platí automaticky).

## Přístup (kdo se smí přihlásit)

Appka vyžaduje přihlášení e-mailovým odkazem (funguje s jakoukoli schránkou, ne jen firemní). Kdo se smí přihlásit, řídí uzel `aquactrl_login_email` (e-mail → kód osoby z `LIDE`):

- Spravuje se přes appku v menu **„Přístup (e-maily)"** (jen pro admina, kód `TŘ`), nebo jednorázově skriptem `seed_login_email.py` (viz jeho hlavička pro použití) přes workflow **„Naplnit povolené e-maily"**.
- Firebase pravidla u `aquactrl_*` uzlů se **zpřísňují až s odstupem** (ne hned s tímhle nasazením) — nejdřív se musí všichni aspoň jednou přihlásit, teprve pak se v konzoli ručně nastaví, že čtení/zápis vyžaduje ověřený e-mail z `aquactrl_login_email`. Do té doby zůstávají `aquactrl_*` uzly přístupné jako dosud.

## Odeslání push notifikace

GitHub → Actions → **Odeslat push (AquaCtrl)** → *Run workflow* (titulek + text, případně Device ID jednoho příjemce). Tokeny se čtou z uzlu `aquactrl_push_tokens` ve sdílené Firebase DB.

## Soubory

| soubor | účel |
|---|---|
| `index.html` | celá appka (UI + data + logika + push) |
| `sw.js` | offline service worker (scope `/aquactrl/`) |
| `firebase-messaging-sw.js` | FCM service worker pro push (scope `/aquactrl/fcm/`) |
| `manifest.json` | PWA manifest |
| `icon-*.png`, `logo-ac-*.png` | ikony / logo (odznak „AC") |
| `send_push_aquactrl.py` | skript pro odeslání FCM push |
| `.github/workflows/send-push.yml` | ruční spuštění push notifikace |
| `seed_login_email.py` | naplnění/doplnění seznamu povolených přihlašovacích e-mailů |
| `.github/workflows/seed-login-email.yml` | ruční spuštění naplnění e-mailů |

## Přejmenování z AquaControl na AquaCtrl

Appka se dřív jmenovala AquaControl. Kód už je celý přepsaný na AquaCtrl (branding, `manifest.json`, cesty `/aquactrl/`, Firebase uzly `aquactrl_*`), ale dvě věci se musí doladit mimo tenhle repo, než se to nasadí:

1. **Přejmenovat GitHub repozitář** (Settings → Repository name → `aquactrl`), jinak GitHub Pages dál poběží na `/aquacontrol/` a nebude sedět s cestami v kódu.
2. **Přesunout data ve Firebase** ze starých uzlů (`aqua_udalosti`, `aqua_ukoly`, `aqua_outbox`, `aqua_zarizeni`, `aqua_push_tokens`, `aqua_login_email`, `aqua_presence`) do nových (`aquactrl_*`). Nejjednodušší přes připravený skript `migrate_aqua_to_aquactrl.py`:
   ```
   python migrate_aqua_to_aquactrl.py --dry-run   # nejdřív zkontroluj, co se zkopíruje
   python migrate_aqua_to_aquactrl.py             # a pak ostrý běh
   ```
   Skript stará data nemaže (zůstanou jako záloha) a cílový uzel přeskočí, pokud už něco obsahuje. Bez téhle migrace appka po nasazení uvidí prázdno (stará data zůstanou v DB, jen se na ně appka přestane dívat).

Po obou krocích si všichni uživatelé budou muset PWA na telefonu **znovu nainstalovat** (starý `scope`/`id` appky se změnil).

## Vývoj

Po každé změně dat/UI v `index.html` bumpni `CACHE` v `sw.js` (kvůli refreshi PWA na mobilech).

Logo source (`logo-ac.png`, 6 MB mockup) zůstal v repu `mojebudky` – zde je jen vyříznutý odznak (`logo-ac-512.png`) a runtime ikony.
