# Manuale FinanceTracker

App offline per le finanze personali. I dati stanno solo sul PC. L’app **propone** (categoria, parola chiave, collegamento prestito); **confermi tu**.

---

## 1. Due numeri, non uno

Ogni movimento tocca il **conto**. Non tutti toccano il **tenore di vita**.


| Cosa guardi                                  | Cosa conta                                                                                                                  |
| -------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **Liquidità**                                | Tutto il cash: spese, stipendi, giri tra conti, prestiti, saldo iniziale, investimenti                                               |
| **Entrate / Uscite / medie / grafici / tasso** | Solo il quotidiano. Fuori: trasferimenti interni, saldo iniziale, prestiti. Gli **investimenti** hanno un KPI loro, non sono uscite |


Se Fineco «sembra ricca» in liquidità e «povera» nel tasso, di solito c’è un giroconto in entrata: soldi già tuoi, non reddito.

**Tasso di risparmio** = (entrate − uscite) / entrate. I rimborsi, se non spunti **Escludi rimborsi**, contano come entrate. I regali restano.

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
- Restano nella liquidità del conto (i soldi sono usciti da Fineco)

Esempio: -50 € Compravendita Titoli. Uscite del mese invariate; liquidità Fineco -50.

### Prestiti

Soldi **tra persone** (o un tab da chiudere), andata e ritorno. Non la rata banca / mutuo: quella è spesa (Casa, Gestione conti, …).

- Fuori da entrate/uscite
- Nella liquidità
- Filtro **Prestiti** in Movimenti: **Prestati / Rientrati / Netto**

**Collegare.** Solo dall’**entrata** Prestiti: *Collega a un prestito* (l’app propone, confermi). L’uscita è la pratica. Con almeno un rientro collegato, in lista vedi **una riga** (aperta o chiusa). **Modifica** mostra uscita e rientri. **Scollega prestito** li separa. **Elimina** toglie tutta la pratica. Se togli la categoria Prestiti, i link cadono da soli.

Esempio: presti 50 € per un bus (−50 Prestiti). Quando tornano (+50 Prestiti) colleghi. Lista: una riga **Chiuso**, 0,00 €. Se torna solo 30 €: una riga **Aperto**, ancora −20 €.

Non usare Prestiti per l’affitto o la spesa del mese: quello è consumo, non un prestito.

### Rimborsi

Soldi che **ti tornano** (reso, assicurazioni, metà conto che paga un altro). È un’entrata vera.

- Restano nelle entrate
- **Escludi rimborsi** sul tasso: non gonfiare il risparmio con i resi
- I **regali ricevuti** non vanno qui: **Regali & Donazioni**

Esempio: −80 € Esselunga. +40 € dal coinquilino → Rimborsi. L’Esselunga non si cancella.

Non collegare rimborso e spesa: non è una pratica come i prestiti. Se la spesa è mista, **dividi** in partenza.

### Regali & Donazioni

Regali fatti o ricevuti, offerte, crowdfunding. Restano nel quotidiano (entrate o uscite). Non sono prestiti.

### Spese speciali (flag, non categoria)

Su un’**uscita** normale: flag **Spesa speciale**.

- L’importo intero resta nei totali e in cassa
- **0 mesi** = fuori dalla **media giornaliera** (una tantum)
- **N mesi** = in media si spalma (abbonamento annuale / 12)

Non è possibile su trasferimenti interni, prestiti, saldo iniziale, investimenti.

Esempio: −120 € Netflix annuale, speciale 12 mesi. In uscite ci sono 120 € associati al mese in cui hai pagato; in media giornaliera pesa come 10 €/mese.

---



## 3. Cosa puoi fare



### Importare

Fineco, PostePay, Revolut, PayPal, più l’inserimento manuale. Scegli il **conto**.

Fineco: se reimporti, la stessa riga (stesso hash) si salta. Un **Autorizzato** può diventare **Contabilizzato** (stesso importo, stesso esercente, date entro 2 giorni). Categoria e note tue restano. Se due coppie sono ambigue, inserisce e segnala «da rivedere».

### Cercare e filtrare

Dashboard e Movimenti: più conti, Entrate / Uscite / Investimenti, mese o **intervallo**. Nessun filtro conti/tipi = tutti.

Prestiti e trasferimenti **non** compaiono se filtri solo Entrate o Uscite: non sono operativi. Per vederli, tipo vuoto (tutti) o categoria Prestiti.

### Modificare

Data, descrizione, categoria, note, flag speciale. L’hash di import **non** cambia: se cambi il testo e reimporti lo stesso file, non duplica.

### Dividere

Un movimento in **2–4** quote, se appartengono a categorie diverse (stesso segno, somma = originale). L’hash resta sulla prima riga: il reimport non crea doppioni. Le altre hanno hash `split-…`.

### Unire

Due o più righe **dello stesso conto**. Resta la più vecchia (hash invariato).

### Annullare

Dopo elimina / unisci / dividi: popup **Annulla** per 15 secondi, non blocca.

### Parole chiave

Dopo un Salva, se c’è qualcosa di nuovo da imparare: proponiamo una keyword. **Aggiungi e ricalcola** aggiorna i movimenti ancora automatici. In Impostazioni le editi a mano.

### Export e backup

Excel in **Download**, si apre la cartella. Backup zip (database + categorie) da Impostazioni; in dashboard vuota puoi **partire da un backup**.

Percorsi dati: Windows `%LOCALAPPDATA%\FinanceTracker\`, Linux `~/.local/share/FinanceTracker/`, macOS `~/Library/Application Support/FinanceTracker/`.

---



## 4. Categorie tue

Puoi crearne, cambiare icona e keyword, rinominare (tranne quelle bloccate). Il nome vecchio non rinasce al riavvio. **Altro** è il resto.

Le keyword sono pezzi di testo dell’estratto (`ESSELUNGA`, `ENI`). 

---



## 5. In due parole

Il conto vede i soldi. Entrate e uscite vedono come vivi. Trasferimenti, saldo iniziale e prestiti sistemano la cassa senza sporcare il mese. Rimborsi e regali restano nel mese; i prestiti si legano in una pratica. In dubbio, non inventare quote: preponderante + nota, oppure lascia il netto in Casa.