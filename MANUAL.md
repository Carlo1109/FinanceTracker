# Manuale FinanceTracker

App offline per le finanze personali, per PC e Android (versione 2.0). I dati stanno sul tuo dispositivo; PC e telefono si allineano con i backup su Google Drive, se lo vuoi. L’app **propone** (categoria, parola chiave, collegamento prestito); **confermi tu**.

---

## 1. Due numeri, non uno

Ogni movimento tocca il **conto**. Non tutti toccano il **tenore di vita**.


| Cosa guardi                                  | Cosa conta                                                                                                                  |
| -------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **Liquidità**                                | Tutto il cash: spese, stipendi, giri tra conti, anticipi e recuperi, saldo iniziale, investimenti                                    |
| **Entrate / Uscite / medie / grafici / tasso** | Solo il quotidiano. Fuori: trasferimenti interni, saldo iniziale, anticipi e recuperi. Gli **investimenti** hanno un KPI loro, non sono uscite |


Se Fineco «sembra ricca» in liquidità e «povera» nel tasso, di solito c’è un giroconto in entrata: soldi già tuoi, non reddito.

**Risparmio** = entrate − uscite. Comprende anche quanto hai **investito** (gli investimenti non sono uscite): il Report lo divide in *investito* e *liquidità*, che sommati fanno il risparmio.

**Tasso di risparmio** = risparmio / entrate. I **Rimborsi** contano come entrate, i regali anche. Un rimborso legato a una tua spesa (assicurazione, metà conto) va in **Anticipi & Recuperi**: vedi sotto.

---



## 2. Categorie speciali

Sono bloccate: non le rinomini e non le elimini (come Altro e Investimenti).

### Trasferimenti interni

Giroconto, ricarica PostePay da Fineco, «passaggio soldi» tra i tuoi conti.

- In lista e nella liquidità
- **Non** in entrate/uscite

Esempio: −500 Fineco e +500 PostePay, entrambi Trasferimenti. La cassa totale non cambia; non hai «speso» 500 €.

### Saldo iniziale

Apri un conto già con dei soldi. Non è uno stipendio.

- In liquidità
- **Non** in entrate

Esempio: apri FinanceTracker a settembre, Fineco ha 2.140 €. Un movimento **Saldo iniziale** +2.140 € in data 1 settembre. Da lì i KPI di cassa tornano.

### Investimenti

PAC, ETF, compravendita titoli.

- KPI **Investimenti** a parte
- **Non** abbassano il tasso di risparmio (li tratti come già messi da parte)
- Nel Report sono **dentro** il risparmio: «Investito 300 € · Liquidità 1.070 €» sotto il totale, e «di cui X% investito» sotto il tasso
- Restano nella liquidità del conto (i soldi sono usciti da Fineco)

Esempio: -50 € Compravendita Titoli. Uscite del mese invariate; liquidità Fineco -50.

### Anticipi & Recuperi

Soldi **tra persone** (o un tab da chiudere), andata e ritorno. Non la rata banca / mutuo: quella è spesa (Casa, Gestione conti, …).

- Fuori da entrate/uscite
- Nella liquidità
- Filtro **Anticipi & Recuperi** in Movimenti: **Prestati / Rientrati / Netto**

**Collegare.** Solo dall’**entrata** Anticipi & Recuperi: *Collega a un prestito* (l’app propone, confermi). L’uscita è la pratica. Con almeno un rientro collegato, in lista vedi **una riga** (aperta o chiusa). **Modifica** mostra uscita e rientri. **Scollega prestito** li separa. **Elimina** toglie tutta la pratica. Se togli la categoria Anticipi & Recuperi, i link cadono da soli.

Esempio: anticipi 50 € per un bus (−50 Anticipi & Recuperi). Quando tornano (+50 Anticipi & Recuperi) colleghi. Lista: una riga **Chiuso**, 0,00 €. Se torna solo 30 €: una riga **Aperto**, ancora −20 €.

Non usare Anticipi & Recuperi per l’affitto o la spesa del mese: quello è consumo, non un prestito.

**Rimborso di una spesa (assicurazione, metà conto).** Quando paghi, l’uscita va nella sua categoria (es. Salute). Se e quando arriva il rimborso:

- **Rimborso totale** (pagati 300 €, rimborsati 300 €): cambia la categoria dell’uscita in Anticipi & Recuperi, metti anche l’entrata in Anticipi & Recuperi e collegale. La pratica si chiude a zero: la spesa non conta più né in uscite né in entrate, anche nel mese in cui l’avevi pagata.
- **Rimborso parziale** (pagati 300 €, rimborsati 200 €): **dividi** l’uscita in 200 € Anticipi & Recuperi + 100 € nella sua categoria, poi collega i 200 € all’entrata. Così in uscite resta solo quello che hai speso davvero (100 €).

Se sposti tutti i 300 € in Anticipi & Recuperi ma te ne tornano 200, i 100 € spesi spariscono dalle uscite e la pratica resta aperta a −100 €.

### Rimborsi

Soldi che **ti tornano** e non sono legati a una tua spesa da sistemare, per esempio dallo **Stato** (rimborso 730, conguaglio in busta paga). È un’entrata vera.

- Contano nelle entrate e nel tasso di risparmio, ovunque (Dashboard e Report)
- I **regali ricevuti** non vanno qui: **Regali & Donazioni**
- Rimborso di una spesa che hai fatto tu (assicurazione, coinquilino che ti ridà la sua metà): **Anticipi & Recuperi**, vedi sopra

Esempio: +350 € rimborso 730 → Rimborsi.

### Regali & Donazioni

Regali fatti o ricevuti, offerte, crowdfunding. Restano nel quotidiano (entrate o uscite). Non sono prestiti.

### Spese speciali (flag, non categoria)

Su un’**uscita** normale: flag **Spesa speciale**.

- L’importo intero resta nei totali e in cassa
- **0 mesi** = fuori dalla **media giornaliera** (una tantum)
- **N mesi** = in media si spalma (abbonamento annuale / 12)

Non è possibile su trasferimenti interni, anticipi e recuperi, saldo iniziale, investimenti.

Esempio: −120 € Netflix annuale, speciale 12 mesi. In uscite ci sono 120 € associati al mese in cui hai pagato; in media giornaliera pesa come 10 €/mese.

Nel **Report**, scheda **Spese speciali**: la Netflix compare in ognuno dei 12 mesi con la sua quota («Rata 3/12 di 120 €», 10 €); una speciale a 0 mesi compare solo nel mese in cui l’hai pagata, per intero.

---



## 3. Cosa puoi fare



### Importare

Fineco, PostePay, Revolut, PayPal, più l’inserimento manuale. Scegli il **conto**.

Fineco: se reimporti, la stessa riga (stesso hash) si salta. Un **Autorizzato** può diventare **Contabilizzato** (stesso importo, stesso esercente, date entro 2 giorni). Categoria e note tue restano, anche se l’Autorizzato l’avevi già modificato (es. cambiando la categoria). Se rinomini la descrizione l’app non riconosce più l’esercente: in quel caso, se resta un doppione, uniscili. Se due coppie sono ambigue, inserisce e segnala «da rivedere».

### Cercare e filtrare

Dashboard e Movimenti: più conti, Entrate / Uscite / Investimenti, mese o **intervallo**. Nessun filtro conti/tipi = tutti.

Anticipi & Recuperi e trasferimenti **non** compaiono se filtri solo Entrate o Uscite: non sono operativi. Per vederli, tipo vuoto (tutti) o categoria Anticipi & Recuperi.

### Report

Pagina **Report**: scegli **Mese** o **Anno** (e, se vuoi, i conti). Due schede: **Riepilogo** e **Spese speciali**.

Il **Riepilogo** ha lo stesso ordine per mese e anno:

1. entrate, uscite, **risparmio** (con sotto *investito* e *liquidità*: le due parti del risparmio) e **tasso di risparmio** (con «di cui X% investito»), col confronto col periodo prima;
2. tre cose «in evidenza» (mese: la categoria cresciuta di più, quella su cui hai risparmiato, la spesa più grande o i giorni senza spese; anno: mese migliore, più caro, categoria principale);
3. l’andamento: nel mese il **calendario** colorato in base a quanto hai speso ogni giorno (tocca un giorno per il dettaglio); nell’anno entrate e uscite **mese per mese** (nel dettaglio di ogni mese anche risparmio e investito) e le **uscite accumulate** contro l’anno prima;
4. le **categorie a confronto** (mese: contro il mese prima e lo stesso mese dell’anno scorso; anno: contro l’anno prima, con la media mensile) e **le spese più grandi**.

La scheda **Spese speciali** elenca le speciali del mese (o dell’anno, mese per mese, fino al mese in corso): le ripartite con la quota del mese, quelle a 0 mesi solo nel mese pagato. Il Riepilogo conta invece le uscite quando le paghi.

Valgono le stesse regole della dashboard: trasferimenti, saldo iniziale e anticipi & recuperi restano fuori; gli investimenti sono a parte.

### Modificare

Tocca (o clicca) una riga della lista per aprire la modifica: data, descrizione, categoria, note, flag speciale. L’hash di import **non** cambia: se cambi il testo e reimporti lo stesso file, non duplica.

### Dividere

Un movimento in **2–4** quote, se appartengono a categorie diverse (stesso segno, somma = originale). L’hash resta sulla prima riga: il reimport non crea doppioni. Le altre hanno hash `split-…`.

### Unire

Due o più righe **dello stesso conto**: **Seleziona** sopra la lista, tocca le righe, poi **Unisci**. Resta la più vecchia (hash invariato).

### Annullare

Dopo elimina / unisci / dividi: popup **Annulla** per 15 secondi, non blocca.

### Parole chiave

Dopo un Salva, se c’è qualcosa di nuovo da imparare: proponiamo una keyword. **Aggiungi e ricalcola** aggiorna i movimenti ancora automatici. In Impostazioni le editi a mano.

### PC e telefono con Google Drive

PC e telefono si allineano con i **backup** passando da una cartella di **Google Drive**. Nessun account in FinanceTracker: usi il tuo Drive.

**Una volta sola**

1. In Google Drive crea una cartella, per esempio **FinanceTracker**.
2. **Sul PC** serve una cartella che si sincronizza con Drive: su Windows e macOS installa *Google Drive per desktop* (Drive compare come disco, es. `G:\Il mio Drive`); su Linux Google non ha un'app ufficiale, usa *Insync* (a pagamento) o *rclone* (gratuito). Se l'app trova Drive imposta da sola la cartella `…\Il mio Drive\FinanceTracker` e la tiene finché non premi **Togli cartella**; altrimenti in Impostazioni → Dati → Backup → **☁️ Cartella condivisa** incolla il percorso, es. `G:\Il mio Drive\FinanceTracker`.
3. **Sul telefono** non serve nulla.

**Dal telefono al PC**

1. Telefono: Opzioni → Dati → **☁️ Salva su Drive** → nella condivisione scegli **Drive** («Salva su Drive»), poi la cartella FinanceTracker e **Salva**.
2. PC: Impostazioni → Dati → Backup → *Da dove?* **Dalla cartella condivisa** → scegli il backup (📱 = telefono, dal più recente) → **Unisci**.

**Dal PC al telefono**

1. PC: **Crea backup completo** → alla domanda «Inviarlo anche alla cartella condivisa?» rispondi **Sì, invia**.
2. Telefono (dopo che Drive l'ha caricato): Opzioni → Dati → *Seleziona un backup* → nell'elenco delle app scegli **Drive** → cartella FinanceTracker → scegli lo zip → **Unisci**.

**Unisci** porta tutto quello che è cambiato sull'altro dispositivo: movimenti nuovi, modifiche e cancellazioni. Se lo stesso movimento è stato cambiato su tutti e due, vince la modifica più recente; quello che hai fatto solo qui non si perde. Lo stesso estratto conto importato su entrambi non crea doppioni. Le categorie nuove si aggiungono. (I backup fatti con versioni prima della 2.0 aggiungono solo i movimenti che mancano.) **Sostituisci** invece mette al posto di tutto il contenuto del backup.

Nella cartella condivisa restano gli ultimi 10 backup di ogni dispositivo. Gli orologi di PC e telefono devono essere giusti (decidono quale modifica è la più recente).

### Export e backup

Excel e backup zip in **Download**, si apre la cartella. Il backup resta anche in archivio locale. In dashboard vuota puoi **partire da un backup**.

Percorsi dati: Windows `%LOCALAPPDATA%\FinanceTracker\`, Linux `~/.local/share/FinanceTracker/`, macOS `~/Library/Application Support/FinanceTracker/`.

---



## 4. Categorie tue

Puoi crearne, cambiare icona e keyword, rinominare (tranne quelle bloccate). Il nome vecchio non rinasce al riavvio. **Altro** è il resto.

Le keyword sono pezzi di testo dell’estratto (`ESSELUNGA`, `ENI`). 

---



## 5. In due parole

Il conto vede i soldi. Entrate e uscite vedono come vivi. Trasferimenti, saldo iniziale e prestiti sistemano la cassa senza sporcare il mese. Rimborsi (es. dallo Stato) e regali restano nel mese; prestiti e rimborsi di una tua spesa si legano in una pratica di Anticipi & Recuperi. In dubbio, non inventare quote: preponderante + nota, oppure lascia il netto in Casa.
