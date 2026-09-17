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

### Přidání nového člověka (postup)

1. **Přístup:** v appce menu **„Přístup (e-maily)"** → e-mail + osoba ze seznamu → *Přidat*.
2. **Pošli mu odkaz** na appku (menu „📤 Sdílet appku"), ať si ji přidá na plochu.
3. **On se přihlásí:** zadá svůj e-mail → přijde mu přihlašovací odkaz → otevře ho
   **na tomtéž zařízení**. (iPhone s appkou na ploše: odkaz v e-mailu zkopírovat a vložit
   v appce do „📱 iPhone".) Přihlášení pak drží trvale.
4. **Identita:** po jeho prvním přihlášení spusť Actions → **„Nastavit identity uživatelů"**,
   ať dostane ověřený claim `person` (appka si token obnoví sama).

### Kdo nemá e-mail — přihlašovací QR

Actions → **„Přihlašovací QR (AquaCtrl)"** → *Run workflow*: zadáš e-mail (kdo žádný nemá,
dostane zástupný, třeba `jan.novak@aquactrl.local` — nemusí existovat), kód osoby z `LIDE`
a případně platnost. Workflow vygeneruje **jednorázový přihlašovací odkaz** přes Admin SDK
(nic se nikam neposílá) a QR se objeví v appce v menu **„Přihlašovací QR"** — vidí ho jen
admin. Dotyčný QR naskenuje z tvého displeje a je přihlášený; e-mail si appka z odkazu vezme
sama, nic neopisuje. Pak už se přihlašovat nemusí. Přes 📤 jde místo skenování poslat i
samotný odkaz (SMS/WhatsApp) — pro iPhone s appkou na ploše je to jistější cesta.

- Odkaz **platí jen jednou** a krátce (výchozí 60 min); po naskenování ho v appce smaž (🗑️).
- **Do GitHub Actions se odkaz nikdy nevypisuje** — repo je veřejné, logy a artefakty vidí
  kdokoli. Proto jde jen do DB (`aquactrl_qr_login`, čte pouze admin), viz
  [SECURITY.md](SECURITY.md#přihlašovací-qr-aquactrl_qr_login). **Bez pravidla pro tenhle uzel
  ve Firebase appka QR nenačte** — pravidlo se přidává v `database.rules.json` v repu `mojebudky`.
- Lokálně (se `service-account-key.json`) totéž udělá
  `python login_qr_aquactrl.py jan.novak@aquactrl.local JN --png qr.png` — QR rovnou do souboru
  k vytištění.

### Kdo které sekce vidí

Menu **„Sekce (kdo co vidí)"** (jen admin): vybereš osobu, zaškrtáš, které části appky vidí,
a uložíš. **Kdo tam není uvedený, vidí všechno** — nastavuje se jen výjimka, u ostatních
se nic měnit nemusí. Hotové nastavení jde tlačítkem 📋 **zkopírovat** a pak ho jedním vložením
nastavit rovnou více lidem najednou (📥 Vložit dalším → zaškrtáš lidi → Použít u vybraných).

Omezení drží i na serveru u **Aktuálních událostí** a **Karet vrtů** (pravidla `aquactrl_pristup_sekce`).
Plán, Kontakty, Čerpadla a Dokumenty jsou natvrdo v `index.html` / v souborech repa, takže
u nich jde jen o skrytí v menu — podrobnosti v [SECURITY.md](SECURITY.md#kdo-které-sekce-vidí-aquactrl_pristup_sekce).

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
| `set_admin_claim.py` | udělení/odebrání admin práv přes Firebase Custom Claim |
| `login_qr_aquactrl.py` | jednorázové přihlašovací QR (pro toho, kdo nemá e-mail) |
| `.github/workflows/login-qr.yml` | ruční vygenerování přihlašovacího QR |
| `.github/workflows/set-admin-claim.yml` | ruční spuštění nastavení admina |
| `check_terminy_aquactrl.py` | ruční/záložní kontrola zmeškaných termínů (viz níže – automaticky to dělá Cloud Function) |
| `SECURITY.md` | náprava po bezpečnostním auditu (Firebase pravidla + admin claim) |

## Přílohy událostí (hlas / foto / dokument) — Firebase Storage

U nové události (krok *Podrobnosti* → *Přílohy*) lze přidat **mluvený popis**
(nahrávka z mikrofonu), **foto** a **dokument**. Soubory se při uložení události
nahrají do **Firebase Storage** (`aquactrl_prilohy/<eventId>/…`) a odkaz se uloží
do uzlu `aquactrl_udalosti/<eventId>/prilohy`. V kartě události (i u souvisejícího
úkolu) se pak zobrazí přehrávač hlasu, náhled fotky a odkaz na dokument.

**Jednorázové nastavení ve Firebase** (bez něj se přílohy nenahrají, událost se
ale uloží normálně):
1. Firebase Console → projekt **moje-budky** → **Storage** → *Get started*
   (bucket `moje-budky.firebasestorage.app`).
2. **Storage → Rules** – povolit `aquactrl_prilohy/**` jen přihlášeným
   (ostatní cesty, pokud je používají budky, nech beze změny):
   ```
   rules_version = '2';
   service firebase.storage {
     match /b/{bucket}/o {
       match /aquactrl_prilohy/{eventId}/{file} {
         allow read, write: if request.auth != null;
       }
       // ... ostatní pravidla (budky) ponech ...
     }
   }
   ```

## Zabezpečení (audit)

Náprava po bezpečnostním auditu (Firebase Security Rules pro `aquactrl_*` + admin
práva přes Custom Claim místo `localStorage`) je popsaná v **[SECURITY.md](SECURITY.md)**
– včetně přesných pravidel k vložení do Firebase konzole a postupu ověření.

## Push notifikace a hlídání termínů (Cloud Functions)

Skutečné odesílání push notifikací a **automatické** hlídání termínů úkolů řeší dvě Cloud Functions v repu [`mojebudky`](https://github.com/pkobelka/mojebudky) (`functions/index.js`), sdílený Firebase projekt `moje-budky`:

- **`aquaNotify`** – trigger na vznik záznamu v `aquactrl_outbox`, pošle FCM push.
- **`aquaUkolyCheck`** – plánovač (každých 15 min): po termínu upozorní zadavatele, řešitele i TŘ (dle pole `upozornit`, které appka od v82 plní automaticky – ruční výběr „koho upozornit" byl zrušen), připomene řešiteli 1 h před termínem, upozorní zadavatele na nepotvrzený úkol.

Tenhle repozitář má vlastní `check_terminy_aquactrl.py` / `.github/workflows/check-terminy.yml`, ale ten je záměrně **jen pro ruční/nouzové spuštění** (automatický cron je vypnutý) — aby lidem nechodilo dvojí upozornění na stejnou věc.

## Přejmenování z AquaControl na AquaCtrl (hotovo)

Appka se dřív jmenovala AquaControl. Přejmenování je dokončené: GitHub repo přejmenováno na `aquactrl`, kód přepsán na branding/cesty/Firebase uzly `aquactrl_*`, data přesunuta skriptem `migrate_aqua_to_aquactrl.py` (starý dry-run/ostrý běh popsaný v jeho hlavičce), Cloud Functions v `mojebudky` přepnuty na nové uzly.

Uživatelé si po přejmenování museli PWA na telefonu znovu nainstalovat (starý `scope`/`id` appky se změnil).

## Vývoj

Po každé změně dat/UI v `index.html` bumpni `CACHE` v `sw.js` (kvůli refreshi PWA na mobilech).

Logo source (`logo-ac.png`, 6 MB mockup) zůstal v repu `mojebudky` – zde je jen vyříznutý odznak (`logo-ac-512.png`) a runtime ikony.
