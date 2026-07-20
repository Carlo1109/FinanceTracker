# Changelog

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
