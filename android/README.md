# 📱 FinanceTracker per Android

È la stessa app Streamlit della versione desktop, eseguita **dentro il telefono e senza internet**:
Streamlit e Python (3.14, in WebAssembly tramite [stlite](https://github.com/whitphx/stlite) e Pyodide)
sono impacchettati nell'APK insieme al codice di `app.py` e `src/`.

Non c'è codice da mantenere due volte. Ogni modifica ai file Python finisce anche nell'APK alla build successiva.

## Come ottenere l'APK

### Una volta sola: la chiave di firma

Tutti gli APK vanno firmati con **la stessa chiave**, altrimenti per aggiornare l'app bisognerebbe
disinstallarla, perdendo i dati.

1. Apri `android/keystore/SEGRETI-GITHUB.txt`. La cartella è esclusa da git e non viene mai caricata.
2. Su GitHub: **Settings → Secrets and variables → Actions → New repository secret** e crea i 4 secret indicati nel file.
3. Conserva una copia di `android/keystore/` in un posto sicuro, per esempio nel password manager.

### Ogni volta

1. Fai push delle modifiche.
2. Su GitHub: **Actions → Android APK → Run workflow**. Ci vogliono circa 10–15 minuti.
3. A fine run, in fondo alla pagina, scarica l'artifact **FinanceTracker-android** (uno zip che contiene l'APK).
4. Sul telefono apri l'APK e conferma l'installazione. La prima volta Android chiede di consentire
   l'installazione da quella app (Chrome, File, …).

### Rilasci (tag)

Quando fai push di un tag `v*`, `release.yml` crea in un'unica run gli installer di Windows, Linux e macOS **e** l'APK,
poi pubblica **una sola Release** con tutti e quattro i file. Se una build fallisce, la Release non esce.

```bash
# dopo aver aggiornato VERSION (es. v1.6.0)
git commit -am "v1.6.0"
git tag v1.6.0
git push && git push --tags
```

### Versioni

- **Versione visibile** (es. 1.6.0): letta dal file `VERSION`, la stessa del desktop.
- **Numero interno** (serve ad Android per riconoscere gli aggiornamenti): è il numero di commit della repo,
  che cresce a ogni commit. Vale sia per le build di prova sia per i rilasci, quindi un APK più recente
  aggiorna sempre quello installato. Ricostruire lo stesso commit dà lo stesso numero: Android lo reinstalla senza problemi.

Nella run trovi anche l'artifact **screenshot-prova**. Prima di creare l'APK, l'app viene avviata in un telefono simulato
**con internet bloccato**: la prova controlla l'avvio offline, tutte le pagine, il salvataggio dei dati dopo un riavvio e la cartella dei dati
(i dati tornano dopo una "reinstallazione").
Se qualcosa non va, la run si ferma lì e il log dice cosa.

## Uso sul telefono

- **Primo avvio e riaperture "a freddo":** 10–30 secondi, il tempo di caricare Python. Se l'app resta in background,
  la riapertura è immediata. Il tasto Indietro, dalla Home, la mette in background senza chiuderla.
- **Dati:** al primo avvio scegli una cartella del telefono, per esempio `Documenti/FinanceTracker`. Lì trovi
  `finance_tracker.db`, `categories.json` e `backups/`, come sul PC: li vedi dall'app File e **restano anche se
  disinstalli l'app**. Reinstallando e scegliendo la stessa cartella, ritrovi tutto. L'app salva nella cartella
  circa 2 secondi dopo ogni modifica e quando va in background. Se un'altra app (per esempio una sincronizzazione)
  cambia il file, FinanceTracker non lo sovrascrive e ti chiede cosa fare. Puoi cambiare cartella da
  *Opzioni → Dati*. Senza cartella i dati restano solo nella memoria interna e si perdono disinstallando.
  In ogni caso non vanno su internet e sono esclusi dal backup automatico di Google.
- **Blocco:** da *Opzioni → Dati* puoi attivare lo sblocco con impronta, volto o PIN del telefono (serve un blocco
  schermo impostato). L'app lo chiede all'apertura e quando ci torni dopo 30 secondi; con il blocco attivo
  screenshot e anteprima nelle app recenti sono nascosti.
- **Backup ed export Excel** finiscono nella cartella **Download** del telefono; i backup anche in `backups/`
  dentro la cartella dei dati.
- **Import:** *Importa* apre il selettore file di Android, quindi puoi usare estratti conto scaricati sul telefono
  o presi da Drive.
- **Dal PC al telefono:** fai un backup sul PC (*Impostazioni → Dati*), copia lo zip sul telefono e, da
  *Opzioni → Dati*, scegli **Unisci al database** (aggiunge solo ciò che manca) o **Sostituisci tutto**.

Requisiti: Android 10 o successivo.

## Cosa c'è qui dentro

| Percorso | Cosa fa |
|---|---|
| `web/index.html` | Pagina di avvio: schermata di caricamento e avvio di stlite |
| `web/android-bridge.js` | Inoltra i download (Excel, backup) all'app nativa |
| `web/native.js` | Cartella dei dati (lettura all'avvio, salvataggi, avviso di conflitto) e controlli del blocco |
| `web/touch.js` | Ritocchi per il touch: menu senza tastiera, dettaglio dei grafici che si chiude da solo |
| `webbuild/build-web.mjs` | Costruisce il bundle offline: Python, pacchetti, codice, font |
| `webbuild/smoke-test.mjs` | Prova offline nel browser prima di creare l'APK |
| `app/` | Progetto Android (Java, nessuna dipendenza): WebView, file, download, cartella dati (`FolderStorage`), blocco |
| `../.github/workflows/android.yml` | Build dell'APK (a mano, o richiamata da `release.yml` sui tag) |
| `../src/theme/mobile.py` | Stile per smartphone: barra in basso, griglie, tocco |
| `../src/utils/platform.py` | `IS_ANDROID`: le differenze per il telefono sono attive solo lì |

La versione desktop non cambia: tutto ciò che riguarda il telefono si attiva solo quando
`FT_PLATFORM=android`, una variabile impostata dalla pagina di avvio dell'app Android.

## Build in locale (facoltativa)

Serve Node 22, JDK 17 e Android SDK.

```bash
cd android/webbuild
npm ci
node build-web.mjs        # crea android/app/src/main/assets/web
node smoke-test.mjs       # prova offline (npx playwright install chromium)
cd ..
gradle assembleRelease    # APK in app/build/outputs/apk/release/
```
