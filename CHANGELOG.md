# Changelog

## v1.4.1

### Funzionalità

- Movimenti: modifica in popup (stesso stile di export e parole chiave)
- Dopo Salva, suggerimento keyword anche se la categoria non è cambiata (solo se c’è qualcosa di nuovo da imparare)
- Lista: **Mostra altri** (40 alla volta) al posto di montare tutte le card

### Interfaccia

- Card movimenti più snelle: barra di tono, chip categoria, flag Nota / Speciale / Escluso
- Overlay dei dialog semitrasparente; form di modifica a tutta larghezza
- Filtro senza risultati: empty state al posto del warning Streamlit
- Impostazioni: liste a card (conti e categorie), modifica categoria / nuova categoria / rimuovi conto in popup; niente expander

## v1.4.0

### Funzionalità

- Dashboard: donut **Da dove arrivano i soldi** (entrate per categoria) e card Fonte principale
- Categoria **Rimborsi** (keyword RIMBORSO / STORNO / RESO / REFUND)
- Movimenti: modifica descrizione, categoria, note e flag da un unico Salva
- **Dividi movimento** in 2–4 quote (categorie diverse; l’hash di import resta sulla prima riga)
- Dopo un cambio categoria: suggerimento di parola chiave (testo modificabile); **Aggiungi e ricalcola** aggiorna le automatiche
- Impostazioni → Dati: percorsi database e categorie copiabili

### Interfaccia

- Sfondo dei donut allineato al grafico andamento mensile
- Colore Rimborsi distinto da Stipendio
- Dopo Salva, se c’è un suggerimento keyword la pagina torna in cima

## v1.3.0

### Funzionalità

- Spese speciali: flag su uscite, ripartizione opzionale su N mesi (media giornaliera) o esclusione totale dalla media; totali di cassa invariati
- Flag **Escludere dalle metriche**: il movimento resta in lista ma non conta in entrate, uscite, medie e grafici
- Categoria **Trasferimenti interni** (giroconto / passaggi tra conti): in lista, esclusi dalle metriche
- Selettore data tematico (giorno / mese / anno) al posto del calendario nativo Streamlit
- Dashboard: sezione Spese speciali espandibile (`N Spese speciali · Totale …`) in card a tema
- Export Excel: colonna esclusione dalle metriche; popup di conferma allineato al tema

### Interfaccia

- Tema chiaro/scuro e card dashboard più coerenti (KPI, distribuzione, andamento, empty state)
- Tooltip help (`?`) leggibili; niente note fisse sotto Spesa speciale / Escludere dalle metriche
- Movimenti: filtro mese **Tutti**, chip stato (speciale / escluso dalle metriche)
- Impostazioni: tasto “Scarica prima i movimenti” più evidente; dialog export a tema
- Pulsanti secondary con sfondo/bordo visibili (si capisce che sono cliccabili)

### Correzioni

- Metriche e grafici ignorano trasferimenti interni e movimenti con flag esclusione
- CSS help Streamlit non rompe più le voci dei menu a tendina
- Grafici Plotly senza tema bianco Streamlit forzato (`theme=None` sul line chart)

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
