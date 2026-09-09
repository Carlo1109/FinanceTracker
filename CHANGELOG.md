# Changelog

## v1.5.2

### Funzionalità

- Categoria **Prestiti** (bloccata): fuori da entrate/uscite/medie, conta nella liquidità del conto. Andata e ritorno nella stessa categoria
- **Regali, Donazioni & Prestiti** diventa **Regali & Donazioni**; i movimenti già in archivio si rietichettano al primo avvio
- Import Fineco: se l’Autorizzato ha l’esercente tronco (`CASCINA GOB` vs `CASCINA G SETTIMO`), unisce comunque se restano almeno due parole lunghe in comune

### Interfaccia

- Movimenti: con filtro categoria **Prestiti**, il riepilogo mostra **Prestati / Rientrati / Netto** (e quanto è ancora aperto sui conti filtrati)
- Nuovo movimento e modifica: caption sui prestiti
- Impostazioni: Prestiti non si rinomina né si elimina

## v1.5.1


### Funzionalità

- Import Fineco: un **Autorizzato** già in archivio diventa **Contabilizzato** se importi lo stesso movimento (stesso conto, stesso importo, stesso esercente, date entro 2 giorni). Categoria e note restano. Se due coppie sono ambigue, non unisce: inserisce e segnala «da rivedere»
- Export Excel: il file si salva in **Download** e si apre la cartella (niente download del browser)

### Interfaccia

- Anteprima import: conteggio **da aggiornare**; Conferma attivo anche se ci sono solo aggiornamenti
- Dopo l’import, niente seconda anteprima dello stesso file
- Importi lunghi sulle card hero/KPI restano su una riga; lo spazio prima di € non va a capo
- Tasso di risparmio: checkbox **Escludi rimborsi**; niente più «senza rimborsi» sotto la percentuale

## v1.5.0

### Funzionalità

- Categoria **Saldo iniziale** (fuori da entrate/uscite, conta nel saldo conto)
- Filtri Dashboard e Movimenti: più conti insieme, **Entrate / Uscite / Investimenti** e **Intervallo personalizzato**
- **Unisci movimenti** (stesso conto; resta la riga più vecchia)
- Impostazioni: **Rinomina categoria** (non Altro, trasferimenti, saldo iniziale, investimenti); il nome vecchio non torna al riavvio
- Liquidità: trasferimenti e saldo iniziale inclusi, così si mostra la cassa reale

### Interfaccia

- Rimosso il flag **Escludere dalle metriche**
- KPI **Liquidità**: cassa cumulativa dei conti filtrati (trasferimenti e saldo iniziale inclusi)
- Modifica movimento: si può cambiare anche la data
- Movimenti: popup **Annulla** dopo elimina, unisci o dividi (non blocca, sparisce dopo 15 s)
- Dashboard vuota: **Parti da un backup**
- KPI **Tasso di risparmio**: flag per escludere i rimborsi (regali e donazioni restano)

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
