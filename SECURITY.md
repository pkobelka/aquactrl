# Zabezpečení AquaCtrl — náprava po bezpečnostním auditu (TNS, 2026-Q3)

Auditor (Trusted Network Solutions) našel **2 nálezy „Vysoká"**. Oba mají jednu
společnou příčinu: **databáze neměla serverovou ochranu.** Tady je náprava a
přesný postup, co udělat ve Firebase.

| # | Nález | Náprava |
|---|-------|---------|
| 1 | Veřejně přístupné kolekce (`aquactrl_*` čitelné/zapisovatelné bez přihlášení) | Firebase pravidla: přístup jen pro přihlášené (`auth != null`) |
| 2 | Obejití přihlášení přes `localStorage` (`ac_person` → admin) | Admin práva z ověřeného Custom Claimu + pravidlo `auth.token.admin` + vyztužený kód appky |

> ⚠️ **Databáze je Realtime Database** (`…firebaseio.com`), ne Firestore, jak omylem
> uvádí report. Syntaxe pravidel je proto jiná (JSON níže).
>
> ⚠️ **DB je sdílená s aplikací „budky".** Pravidla jsou **jeden** dokument pro celou
> databázi. V Kroku 3 měň jen uzly `aquactrl_*`; uzly budek nech přesně jak jsou,
> jinak je rozbiješ. (Kompletní finální dokument je v Kroku 3.)

---

> ❗ **Zdroj pravdy pro pravidla = `database.rules.json` v repu [`mojebudky`](https://github.com/pkobelka/mojebudky).**
> Firebase RTDB je sdílená a workflow „Deploy Firebase" v `mojebudky` při každém nasazení
> **přepíše** pravidla v konzoli tímhle souborem. Proto se pravidla **musí měnit tam**
> (ne jen ručně v konzoli, jinak je příští deploy zahodí). Zabezpečené `aquactrl_*` uzly
> jsou už v tom souboru (commit „database.rules: zabezpečení aquactrl_* uzlů").

## Postup (pořadí je důležité, ať se nezamkneš)

### Krok 1 — Udělej si admina (Custom Claim)
GitHub → **Actions** → **„Nastavit admina (AquaCtrl)"** → *Run workflow*
- `email`: e-mail, kterým se **přihlašuješ do appky** (default `petr.kobelka@vhos.cz` — pokud loguješ jiným, zadej ten)
- `akce`: `set`
- Spusť. (Běží přes stejný `FIREBASE_SERVICE_ACCOUNT` secret jako ostatní workflow.)

### Krok 2 — Přihlas se v appce znovu
Odhlas se a znovu přihlas e-mailovým odkazem (nebo appku zavři a otevři).
Tím si stáhneš token s admin claimem. Po tomhle ti zase naskočí admin menu
(„Přístup (e-maily)", „Zařízení").

### Krok 3 — Zapni pravidla ve Firebase
Firebase Console → projekt **moje-budky** → **Realtime Database** → záložka **Rules**.

> ⚠️ **Pozor:** databáze už `aquactrl_*` klíče obsahovala (dole v dokumentu), a byly
> **otevřené** (`".read": true, ".write": true`) — přesně to je nález 1. Nejde je jen
> „přidat" (vzniknou duplicity a Publish selže). Je potřeba je **sjednotit do jednoho**.
> Níže je **kompletní finální dokument**, jak byl publikován: `aquactrl_*` zabezpečené,
> ostatní uzly (budky) beze změny. Zkontroluj proti své verzi a **nahraď** (Ctrl+A →
> vložit → Publish). Uzly pro budky si předtím ověř, ať ti tam sedí všechny.

```json
{
  "rules": {
    ".read": false,
    ".write": false,

    "aquactrl_udalosti":    { ".read": "auth != null", ".write": "auth != null" },
    "aquactrl_ukoly":       { ".read": "auth != null", ".write": "auth != null", ".indexOn": ["resitel", "stav"] },
    "aquactrl_absence":     { ".read": "auth != null", ".write": "auth != null" },
    "aquactrl_zarizeni":    { ".read": "auth != null", ".write": "auth != null" },
    "aquactrl_presence":    { ".read": "auth != null", ".write": "auth != null" },
    "aquactrl_push_tokens": { ".read": "auth != null", ".write": "auth != null" },
    "aquactrl_outbox":      { ".read": "auth != null", ".write": "auth != null" },
    "aquactrl_login_email": { ".read": "auth != null", ".write": "auth.token.admin === true" },
    "aquactrl_qr_login":    { ".read": "auth.token.admin === true", ".write": "auth.token.admin === true" },
    "aquactrl_karty_vrtu":  { ".read": "auth != null && (…viz aquactrl_pristup_sekce…)", ".write": "auth != null" },
    "aquactrl_pristup_sekce": { ".read": "auth.token.admin === true", ".write": "auth.token.admin === true",
                                "$kdo": { ".read": "auth != null && (auth.token.admin === true || auth.token.person === $kdo)" } },

    "presence":           { ".read": true, ".write": true },
    "aktivita":           { ".read": true, ".write": true },
    "budky_edit":         { ".read": true, ".write": true },
    "admin_requests":     { ".read": true, ".write": true },
    "spravci":            { ".read": true, ".write": true },
    "spravce_aktivita":   { ".read": true, ".write": true },
    "prihlaseni":         { ".read": true, ".write": true },
    "navstevnost_log":    { ".read": true, ".write": true, ".indexOn": ["ts"] },
    "navstevnost_celkem": { ".read": true, ".write": true },
    "push_broadcast":     { ".read": true, ".write": true },
    "push_history":       { ".read": true, ".write": true },
    "push_tokens":    { "$id": { ".read": true, ".write": true } },
    "zpravy_spravci": { "$loginId": { ".read": true, ".write": true } },
    "hesla":          { "$uid": { ".read": true, ".write": true } }
  }
}
```

Co to dělá:
- **`aquactrl_login_email`** (řídí, kdo se smí přihlásit) smí **měnit jen admin** → zavírá nález 2 na serveru.
- **`aquactrl_qr_login`** (čekající přihlašovací QR, viz níže) smí **číst i měnit jen admin** —
  leží v něm jednorázový přihlašovací odkaz, takže ho nesmí vidět ani ostatní přihlášení.
- **`aquactrl_pristup_sekce`** (kdo které sekce vidí, viz níže) mění jen admin; každý si smí
  přečíst jen **svůj** záznam, celý seznam vidí admin.
- **`aquactrl_karty_vrtu`** v pravidlech dřív **vůbec nebyl**, takže ho kořenové `".read": false`
  blokovalo a sekce „Karty vrtů" hlásila `Permission denied`. Teď má pravidlo jako ostatní.
- Všechny ostatní `aquactrl_*` uzly jsou přístupné **jen přihlášeným** → zavírá nález 1.
- `.indexOn` u `aquactrl_ukoly` zůstává kvůli dotazu appky přes `orderByChild("resitel")`.
- **Nikoho to nevyhodí:** appka už dnes přihlášení vyžaduje. GitHub Actions skripty i
  Cloud Functions jedou přes admin SDK, ten pravidla obchází → push, hlídání termínů
  i „Naplnit e-maily" fungují dál.

> 📌 **Mimo tento audit:** uzly budek (`hesla`, `budky_edit`, …) zůstávají `true/true`.
> Bezpečnostně by je stálo za to taky zavřít, ale to je věc aplikace „budky", ne AquaCtrl.

### Krok 4 — Ověř nápravu (re-test)
1. **Anonymní přístup:** v anonymním okně (bez přihlášení) otevři
   `https://moje-budky-default-rtdb.firebaseio.com/aquactrl_udalosti.json` →
   musí vrátit `Permission denied` (dřív vracelo data). ✅ nález 1
2. **Podvržení admina:** přihlas se **jako běžný uživatel**, v F12 dej
   `localStorage.setItem('ac_person','TŘ')` a obnov stránku → admin menu se
   **neobjeví** (kód čte claim, ne localStorage). A i kdyby, zápis do
   `aquactrl_login_email` pravidlo odmítne. ✅ nález 2

---

## Přihlašovací QR (`aquactrl_qr_login`)

Kdo nemá e-mail, dostane **jednorázový přihlašovací odkaz** vygenerovaný Admin SDK
(workflow „Přihlašovací QR (AquaCtrl)" → `login_qr_aquactrl.py`) a naskenuje ho jako QR.

> ⚠️ **Odkaz je plnohodnotný klíč do appky** (přihlásí kohokoli, kdo ho otevře, jako
> danou osobu). Repozitář je **veřejný**, takže logy i artefakty běhů Actions si může
> stáhnout kdokoli — odkaz se proto do Actions **nikdy nevypisuje**. Workflow ho uloží
> jen do `aquactrl_qr_login` a appka ho ukáže pouze adminovi (menu „Přihlašovací QR").
> Skript má i pojistku: přepínač `--odkaz` v prostředí GitHub Actions odmítne běžet.

Další ochrany: odkaz **platí jen jednou** (Firebase ho po použití zneplatní) a má
krátkou platnost (výchozí 60 min, `--minut`). Prošlé pozvánky skript maže při každém
běhu, admin je může smazat i ručně v appce (🗑️) hned po naskenování.

**Bez pravidla `aquactrl_qr_login` výše appka QR nenačte** (kořenové `".read": false`
ho zablokuje) a v „Přihlašovací QR" se objeví hláška o chybějícím pravidle. Pravidlo se
— jako všechna ostatní — mění v `database.rules.json` v repu
[`mojebudky`](https://github.com/pkobelka/mojebudky), ne jen v konzoli.

## Kdo které sekce vidí (`aquactrl_pristup_sekce`)

Admin může jednotlivým lidem schovat části appky (menu „Sekce (kdo co vidí)"). Uzel
`aquactrl_pristup_sekce/<kód osoby>` drží mapu `sekce -> true/false`; **kdo v uzlu není,
vidí všechno**, takže pro naprostou většinu lidí se nenastavuje nic. Admin vidí vždy vše.

Co to opravdu zamyká:

| sekce | vynuceno pravidly? |
|---|---|
| Aktuální události | **ano** — bez práva nejde načíst seznam `aquactrl_udalosti`. Jednotlivá událost podle ID zůstává čitelná všem přihlášeným, aby fungoval odkaz z úkolu a z cisteren. |
| Karty vrtů | **ano** — `aquactrl_karty_vrtu`. |
| Moje úkoly | částečně — appka je už dnes čte dotazem „kde jsem řešitel". |
| Plán vzorkování, Kontakty, Čerpadla, Dokumenty | **ne** — data jsou natvrdo v `index.html`, případně jako soubory v repu, a ten je veřejný. Skrytí v menu je jen pro přehlednost, ne utajení. |

> ⚠️ Kdo ještě nemá claim `person` (nespustil se pro něj `sync_person_claims.py`), na tyhle
> uzly dosáhne — pravidlo v takovém případě záměrně pouští dál, aby se nikomu nerozbila
> appka dřív, než se claimy nastaví. U omezovaného člověka proto claim nastav.

Cisterny se nastavují společně s událostmi (rezervace jsou uložené uvnitř událostí) —
appka to hlídá sama: odškrtnutí událostí odškrtne i cisterny.

## App Check (volitelné doporučení z auditu)

App Check omezuje přístup k Firebase jen na ověřené instance tvojí appky. Kód je
už připravený (`index.html` → `firebase.appCheck().activate(...)`), jen je **vypnutý**,
dokud nevložíš site key. **Dokud je `APPCHECK_SITE_KEY` prázdný, nic se neděje.**

> ⚠️ **POZOR — sdílená databáze s „budkami".** App Check *enforcement* se zapíná
> pro celý produkt (celou Realtime Database), ne per aplikace. Pokud vynutíš App Check
> na RTDB dřív, než i appka **budky** posílá App Check tokeny, **rozbiješ budky.**
> Proto níže enforcement nejdřív jen **monitoruj**, ostré vynucení až po instrumentaci budek.

Postup:
1. **Registruj appku:** Firebase Console → **App Check** → vyber svou web app →
   provider **reCAPTCHA v3** → vygeneruj/vlož **site key**. Přidej doménu
   `pkobelka.github.io` do povolených domén reCAPTCHA klíče.
2. **Vlož klíč do kódu:** v `index.html` nastav `var APPCHECK_SITE_KEY='6Lc…';`
   (bump `VERZE` + `CACHE` v `sw.js`), commitni a nasaď. Appka začne posílat App Check tokeny.
3. **Sleduj metriky:** App Check → záložka s produktem **Realtime Database** → nech
   běžet v režimu **Monitor** (neblokuje), dokud podíl „ověřených requestů" nevyskočí nahoru.
4. **Vynuť (Enforce)** na RTDB **teprve až** i budky posílají tokeny — jinak budky spadnou.
   (Vynucení na FCM/ostatní produkty lze zapnout dřív, pokud je jiné appky nepoužívají.)

Bez App Check jsou **oba nálezy „Vysoká" už i tak zavřené** (pravidla + admin claim výše).
App Check je obrana navíc.

## Poznámky
- **Odebrat admina** komukoliv: stejný workflow s `akce: remove`.
- Appka bere admina z `user.getIdTokenResult()` (viz `jsemAdmin()` v `index.html`).
  `ac_person` v localStorage zůstává jen jako UX pomůcka (kdo jsem), ne jako
  bezpečnostní hranice.
- Report je **TLP:AMBER** → nesdílej ho mimo okruh, kterého se týká.
