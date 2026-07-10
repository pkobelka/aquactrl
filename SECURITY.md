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
