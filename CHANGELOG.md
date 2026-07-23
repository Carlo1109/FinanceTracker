# Changelog

## v1.2.0

### Funzionalità

- KPI e confronti periodo centralizzati in `analytics` (usati da Dashboard e Movimenti)
- Confronti Δ con intervallo date esplicito (es. `1–23 lug vs 1–23 giu`)
- Indicatore “Dati aggiornati al …” in Dashboard
- Export Excel brandizzato (logo + FinanceTracker / Personal Finance Manager) con popup di conferma
- Rimozione conto da Impostazioni (cancella i movimenti dal DB, con conferma forte ed export preliminare)
- Info privacy: app offline, dati locali, senza cloud

### Interfaccia

- Movimenti, Nuovo movimento e Importa dati allineati alle card della Dashboard
- Empty state Movimenti con CTA verso import / nuovo movimento
- Anteprima import con KPI card al posto delle metriche native

### Correzioni

- Warning openpyxl su Excel banca senza stile default (silenziati in lettura)
- Parsing date import più deterministico (niente warning “Could not infer format”)
- Packaging PyInstaller: `analytics`, export Excel, `openpyxl` / Pillow

### Rimosso

- Pagina Analisi (ridondante rispetto alla Dashboard)

## v1.1.0

### Funzionalità

- Backup completo e ripristino da file zip
- Colori categoria persistenti e unici
- Navigazione estratta in componente dedicato

### Correzioni

- Gestione date più robusta (gli inserimenti manuali non rompono più ordinamento/filtri)
- Import senza data operazione non genera più errore
- Import Fineco: importo `0` non classificato come uscita
- Upload file su Linux (WebKit): il dialog di sistema mostra correttamente i file in Download
- Moduli mancanti nel build PyInstaller (navigazione / components)

### Interfaccia

- UI aggiornata (tema, tipografia, card, colori verde/rosso per entrate/uscite)
- Grafico a torta uscite con ombra e highlight al passaggio del mouse
- Dashboard e liste movimenti più pulite

## v1.0.1

Stesse funzionalità di v1.0.0.

### Packaging

- Installer Linux (`.deb`) via GitHub Actions
- App macOS (`.app` nello zip) via GitHub Actions
- Installer Windows (Inno Setup `.exe`) via GitHub Actions

## v1.0.0

Prima release pubblica.

### Dashboard

- KPI
- Grafico a torta

### Movimenti

- Import Fineco
- Inserimento manuale
- Modifica categorie

### Impostazioni

- Backup
- Gestione categorie
- Gestione keyword

### Desktop

- Applicazione Windows
- Database locale
- Nessun cloud

