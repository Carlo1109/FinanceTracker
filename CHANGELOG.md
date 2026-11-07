# Changelog

## v1.7.0

### Funzionalità

- Backup: oltre a **Sostituisci tutto** c’è **Unisci al database**, che aggiunge solo i movimenti e le categorie mancanti (riconosciuti come negli import) senza cancellare nulla. I collegamenti dei prestiti restano corretti. Serve per allineare PC e telefono
- Android: **blocco con impronta, volto o PIN** del telefono, all’apertura e dopo 30 secondi in background; con il blocco attivo screenshot e anteprima nelle app recenti sono nascosti
- Android: **Opzioni → Dati** spiega dove stanno i dati (memoria privata dell’app) e dove finiscono backup ed export (Download), e contiene il blocco dell’app

### Interfaccia

- Riattivati gli stili che con Streamlit 1.58 non venivano più applicati: righe movimento compatte con barra colorata per entrate/uscite, pannelli di dashboard e impostazioni, pulsanti a pillola (**Modifica**, **Esporta**, **Rimuovi**)
- Font Manrope e Fraunces inclusi nell’app: l’aspetto è corretto anche senza internet (prima venivano da Google Fonts)
- Android, popup e tocco: dialog a tutto schermo che scorrono al loro interno, pulsante di chiusura grande e sempre visibile, pulsanti affiancati (Conferma/Annulla), griglia delle icone su più colonne, ✕ delle parole chiave piccolo e accanto alla parola, menu a tendina che non aprono la tastiera, messaggi in basso che non coprono i dialog, dettaglio dei grafici che sparisce da solo dopo il tocco
- Messaggi di conferma (es. «Movimento salvato»): fondo pieno e leggibile, un solo bordo con barra colorata, testo più grande (anche su desktop)
- Card della dashboard (spesa principale, fonte principale, spesa media, tasso di risparmio): sempre della stessa altezza, anche con testi su più righe
- Android: grafico a ciambella nativo, sempre trasparente sul tema dell’app (prima poteva avere il fondo bianco con il telefono in tema scuro)
- Android: tutte le card della dashboard (Entrate, Uscite, Investimenti, Liquidità e le card informative) hanno la stessa identica misura; confronti più brevi («vs prec.»)
- Android: menu a tendina rinnovati, con campo unico arrotondato, voci più alte e la voce scelta evidenziata con ✓
- Android: i testi dei pulsanti non vengono più tagliati con «…» (vanno a capo; «Scegli» per i colori); nella dashboard vuota i pulsanti sono uno sotto l’altro

### Prestazioni

- I grafici a ciambella non si ricaricano più a ogni interazione se i dati non cambiano
- Grafico mensile tenuto in memoria finché dati e colori non cambiano: la dashboard si aggiorna più in fretta
- Android: niente sfocature, ombre più leggere, nessuna animazione o pagina sbiadita a ogni aggiornamento, controlli della pagina raggruppati una volta per fotogramma: scorrimento e tocchi più fluidi

### Build

- Test automatici (`pytest`) su import delle banche, calcoli, movimenti e backup; girano nella Release prima della pubblicazione
- `requirements.txt` contiene solo l’app; `requirements-build.txt` aggiunge PyInstaller, `requirements-dev.txt` aggiunge i test
- La build Android usa gli stessi font del desktop (`static/fonts`)

## v1.6.0

### Funzionalità

- **App Android** offline: stesse pagine e stesso stile del desktop, con Python e Streamlit dentro l’app (nessuna connessione). I dati restano sul telefono, esclusi dal backup automatico di Google
- Android: Excel e backup si salvano in **Download**; import estratti conto e ripristino backup dal selettore file del telefono
- Per passare i dati dal PC al telefono: backup dal desktop, ripristino da **Opzioni → Dati**

### Interfaccia

- Android: barra di navigazione in basso, card KPI in griglia 2×2, righe movimento compatte, data su una riga, dialog a tutta larghezza
- Android: grafici pensati per il tocco (dettaglio al tocco, niente zoom che blocca lo scroll, etichette dei mesi leggibili)
- Android: font Manrope e Fraunces inclusi nell’app

### Prestazioni

- Movimenti tenuti in memoria e ricaricati solo quando il database cambia; date lette in blocco. Ogni interazione è molto più rapida, anche su desktop (circa 2 s → 0,1–0,3 s con 1.500 movimenti)

### Build

- Nuovo workflow **Android APK** (`android.yml`): bundle offline, prova nel browser con internet bloccato, APK firmato
- `release.yml` crea anche l’APK e pubblica **una sola Release** con Windows, Linux, macOS e Android

## v1.5.6

### Build

- Release Linux: runner fissato a Ubuntu 24.04 per garantire la compatibilità di PyGObject con Python 3.12; aggiornate le GitHub Actions al runtime Node.js 24

## v1.5.5

### Bugfix

- Unisci movimenti: conserva gli hash dei movimenti originali, così il reimport non li reinserisce come duplicati; gli hash vengono ripristinati anche annullando l’unione

## v1.5.4

- Categoria **Prestiti** rinominata **Anticipi & Recuperi**; i movimenti già archiviati si aggiornano al primo avvio

## v1.5.3

### Funzionalità

- **Prestiti**: dal rientro si collega all’uscita (l’app propone, confermi). Un’uscita, più rientri, anche parziali e su conti diversi
- Lista Movimenti: pratica collegata = **una riga** (**Aperto** col residuo, o **Chiuso** a 0,00 €)
- **Modifica** apre la pratica: uscita e rientri insieme. **Scollega prestito** li separa; **Elimina** toglie tutta la pratica
- Se togli la categoria Prestiti, i collegamenti cadono da soli
- **Manuale** (`MANUAL.md`): Manuale per capire di più su categorie speciali, split, import e prestiti

### Interfaccia

- Dialog prestito: chip **Prestiti · Aperto/Chiuso** e card dei movimenti della pratica
- **Scollega prestito** accanto a **Dividi movimento**
- Backup: come l’Excel, si salva in **Download** e si apre la cartella (su Windows il tasto Scarica del browser non partiva)
- Pratica con rientro un filo sopra: in lista e nel menu resta **chiuso**; il dettaglio sta in modifica

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
