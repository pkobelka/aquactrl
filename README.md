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
| `check_terminy_aquactrl.py` | ruční/záložní kontrola zmeškaných termínů (viz níže – automaticky to dělá Cloud Function) |

## Push notifikace a hlídání termínů (Cloud Functions)

Skutečné odesílání push notifikací a **automatické** hlídání termínů úkolů řeší dvě Cloud Functions v repu [`mojebudky`](https://github.com/pkobelka/mojebudky) (`functions/index.js`), sdílený Firebase projekt `moje-budky`:

- **`aquaNotify`** – trigger na vznik záznamu v `aquactrl_outbox`, pošle FCM push.
- **`aquaUkolyCheck`** – plánovač (každých 15 min): upozorní po termínu, připomene 1 h před termínem, upozorní zadavatele na nepotvrzený úkol.

Tenhle repozitář má vlastní `check_terminy_aquactrl.py` / `.github/workflows/check-terminy.yml`, ale ten je záměrně **jen pro ruční/nouzové spuštění** (automatický cron je vypnutý) — aby lidem nechodilo dvojí upozornění na stejnou věc.

## Přejmenování z AquaControl na AquaCtrl (hotovo)

Appka se dřív jmenovala AquaControl. Přejmenování je dokončené: GitHub repo přejmenováno na `aquactrl`, kód přepsán na branding/cesty/Firebase uzly `aquactrl_*`, data přesunuta skriptem `migrate_aqua_to_aquactrl.py` (starý dry-run/ostrý běh popsaný v jeho hlavičce), Cloud Functions v `mojebudky` přepnuty na nové uzly.

Uživatelé si po přejmenování museli PWA na telefonu znovu nainstalovat (starý `scope`/`id` appky se změnil).

## Vývoj

Po každé změně dat/UI v `index.html` bumpni `CACHE` v `sw.js` (kvůli refreshi PWA na mobilech).

Logo source (`logo-ac.png`, 6 MB mockup) zůstal v repu `mojebudky` – zde je jen vyříznutý odznak (`logo-ac-512.png`) a runtime ikony.
