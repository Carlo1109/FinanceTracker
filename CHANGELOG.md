# Changelog

## v2.0.0

Nuova grafica, app più leggera sul telefono, pagina Report e passaggio dei dati tra PC e telefono con Google Drive.

> Al primo avvio il database si aggiorna da solo (servono i nuovi campi per l'unione dei backup). Fai un backup prima di aggiornare, per sicurezza.

### Funzionalità

- **PC ↔ telefono con Google Drive**: «Crea backup» sul PC chiede se inviarlo anche alla cartella condivisa (una cartella di Drive sul PC); sul telefono c'è **☁️ Salva su Drive** («Salva in…» di Android). Per importare, sul PC si sceglie il backup direttamente dalla cartella condivisa (📱/💻, dal più recente); sul telefono dal selettore file, dove c'è Drive. Nella cartella restano gli ultimi 10 backup per dispositivo
- **Unisci più intelligente**: con i backup della v2.0 arrivano anche modifiche e cancellazioni fatte sull'altro dispositivo (vince la modifica più recente), non solo i movimenti nuovi; lo stesso estratto conto importato su entrambi non si duplica; anticipi e recuperi restano collegati
- I nomi dei backup dicono da quale dispositivo arrivano (`..._pc.zip`, `..._telefono.zip`)
- Nuova pagina **Report**: mensile (entrate, uscite, risparmio e tasso di risparmio con il confronto col mese prima, tre cose «in evidenza», calendario delle uscite giorno per giorno, spese più grandi, categorie contro il mese prima e lo stesso mese dell’anno scorso) e annuale (mese per mese, uscite accumulate anno su anno, mese migliore e più caro, categorie con media mensile), con lo stesso ordine nelle due viste
- Report: sotto il **risparmio** quanto ne hai **investito** e quanto è rimasto **liquidità** (le due parti del risparmio, non un numero in più); sul tasso di risparmio «di cui X% investito»; nell'anno l'investito totale e, in «Mese per mese», risparmio e investito di ogni mese
- Report: scheda **Spese speciali** (mese e anno): le ripartite su N mesi compaiono in ogni mese con la quota («Rata 3/12 di 120 €»), quelle a 0 mesi solo nel mese in cui le hai pagate; nell'anno raggruppate per mese (chiusi, si aprono toccando il mese), fino al mese in corso. Il Riepilogo resta di cassa
- Rimborsi sempre tra le entrate, in Dashboard e Report: tolta la casella «Escludi rimborsi», che toglieva il rimborso anche dal risparmio mentre la spesa restava intera. I rimborsi legati a una spesa (assicurazione, metà conto) si gestiscono con Anticipi & Recuperi (vedi MANUAL); Dashboard e Report calcolano il tasso allo stesso modo
- Movimenti: la lista è raggruppata per giorno («Oggi», «Ieri», «Venerdì 7 novembre») con il totale del giorno; si tocca la riga per modificarla. Per unire: **Seleziona**, tocca le righe, **Unisci**

### Interfaccia

- Grafica rinnovata, chiara e scura: superfici più pulite, card KPI con icona e variazione in un’etichetta colorata, card principale con la liquidità e il suo andamento negli ultimi 12 mesi (il bilancio del periodo passa tra le card sotto), importi con cifre allineate (Manrope), investimenti in viola
- Nuovi grafici (ciambella, andamento mensile, barre, calendario) disegnati in SVG, con il dettaglio al passaggio del mouse o al tocco; stesso aspetto su PC e telefono
- Menu laterale più compatto sul PC; filtri della dashboard su una riga
- Android: barra in basso con **Report**; «Nuovo» con un + semplice (l'emoji ➕ su alcuni telefoni, es. Samsung, è un quadrato blu); filtri di Home e Movimenti in un riquadro richiudibile (la ricerca resta sempre visibile) che non si richiude scegliendo periodo, conto o tipo, col riepilogo dei filtri nella riga sotto; card più basse
- Android: logo non più deformato nella schermata di caricamento e nella barra in alto; su Android 12+ anche la schermata di avvio di sistema mostra il logo intero
- Android: nei menu a tendina (es. Categoria nella modifica di un movimento) le ultime voci non restano più tagliate fuori
- Android: tabella delle categorie del report più compatta, entra nello schermo
- Dashboard: sotto «Spesa media giornaliera» una riga corta («su 30 giorni · 2 speciali»); il dettaglio è nella sezione Spese speciali
- Dashboard: il tasso di risparmio ha il confronto col periodo prima, in punti («↑ 4,1 pt vs prec.»)
- Android: tolta la frase sul selettore dei file nel ripristino del backup
- Android: dopo aver aperto e chiuso un movimento la riga non resta più grigia
- PC: «Crea backup» salva lo zip in Download senza aprire la cartella
- Dopo «Unisci» o «Sostituisci» resta un messaggio verde con l'esito (prima il toast spariva col ricaricamento)
- PC: la cartella condivisa si imposta da sola se c'è Google Drive (`…/Il mio Drive/FinanceTracker`) e resta impostata finché non la togli; è salvata in un file del PC (`shared_folder.txt`), così nessun backup la cambia

### Prestazioni

- Lista movimenti disegnata come un unico elemento (prima ~10 per riga): molti meno elementi a ogni interazione, e spuntare le righe da unire non ricarica più la pagina
- Il riquadro «Vuoi tornare indietro?» non riesegue più l’app ogni secondo (il tempo scorre con un’animazione)
- Dashboard e Report tengono in memoria i calcoli finché dati e filtri non cambiano
- Le pagine vengono caricate solo quando si aprono; openpyxl solo quando si esporta in Excel; preferenze e controllo del database non vengono riletti a ogni interazione
- Plotly rimosso: niente pacchetto da installare e importare all’avvio del telefono, niente plotly.js nella WebView
- Android: lo stile dell’app (~110 KB) è un file caricato una volta sola all’avvio (`ft.css`); a ogni interazione si inviano solo le variabili del tema

### Correzioni

- Import Fineco: un **Autorizzato** già modificato (es. cambiando solo la categoria) a volte non veniva aggiornato dal suo **Contabilizzato** e restava doppio: salvando, la descrizione completa finiva anche in quella breve e il confronto falliva. Ora, se la descrizione non cambia, restano quelle della banca, e il confronto ignora le parole doppie (si abbinano anche gli Autorizzati modificati in passato)

### Build

- `build-web.mjs` genera `ft.css` e non include più plotly; la prova offline controlla anche lista movimenti, grafici e Report
- Test per i report (`tests/test_reports.py`: anche investito nel risparmio, rimborsi nel tasso, spese speciali mese per mese), per l'unione dei backup e la cartella condivisa (`tests/test_backup_merge.py`) e per l'Autorizzato modificato che si abbina al Contabilizzato (`tests/test_imports.py`)
- Database: nuove colonne `uid` e `updated_at`, tabella `sync_tombstones` e trigger che le tengono aggiornate (migrazione automatica al primo avvio)
- Android: «☁️ Salva su Drive» usa la condivisione di Android (nuovo `ShareProvider`, metodo nativo `shareFile`): lì c'è sempre «Salva su Drive», mentre «Salva in…» su molti telefoni non mostra Drive
- Android: scegliendo un file da importare (backup o estratto conto) si apre l'elenco delle app, con Drive tra le prime, invece del solo selettore file

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
- Android: menu a tendina rinnovati, con campo unico arrotondato e la voce scelta evidenziata con ✓; le ultime voci degli elenchi lunghi (es. Disinvestimenti, Anticipi & Recuperi) si vedono sempre
- Android: date con il mese in numero (es. 07 / 11 / 2026), sempre leggibili per intero
- Android: nel grafico mensile l’asse mostra solo il primo e l’ultimo mese (il mese di ogni punto compare toccandolo)
- Android: riquadro «Vuoi tornare indietro?» sopra la barra in basso, a tutta larghezza; nelle finestre il titolo resta fisso in alto e la ✕ non copre più i movimenti di un anticipo
- Android: tasso di risparmio solo con la percentuale, la casella «Escludi rimborsi» non copre più nulla
- Android: le spiegazioni dei «?» restano dentro lo schermo e vanno a capo
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
