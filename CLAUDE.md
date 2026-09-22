# Spesa — memoria di progetto

Leggi tutto questo file prima di toccare qualsiasi cosa.
La storia lunga, col perché di ogni scelta, sta in **`NOTE.md`** (1200 righe):
vacci quando questo file non basta, e **prima di rifare qualcosa che sembra
mancare** — quasi sempre è già stato provato e c'è scritto com'è andata.

**Esiste anche `AGENTS.md`, copia di questo file** fatta il 2026-09-22 perché
Manlio prova il progetto con un altro programma (Antigravity) oltre a Claude.
**Chi aggiorna questo file aggiorni anche quello**, almeno la parte «Da fare
adesso»: se restano diversi, la prossima sessione — di uno dei due programmi —
parte da informazioni vecchie.

## Chi è l'utente e come lavora

Manlio. **Non legge il codice** e non usa il terminale. Verifica il lavoro in un
solo modo: apre l'indirizzo sul telefono e guarda se l'app fa quello che deve.

Conseguenze operative, e non sono formalità:
- **Spiegagli cosa cambia PER LUI, non cosa hai fatto tu.** Il 2026-09-06 gliel'ho
  raccontata al contrario — pagine lette, controlli aggiunti, percentuali — e lui:
  «io da quello che c'è scritto non lo capisco, io ti ho chiesto di migliorare
  un'applicazione». Aveva ragione. Quanto lavoro è costato non è un risultato.
- Non chiedergli di leggere un diff, un file, un numero di riga.
- Un file in una cartella temporanea, per lui, **non esiste**: se deve averlo,
  serve un indirizzo pubblico.
- Scrivi in italiano.
- Non lasciare mai il repo in uno stato non funzionante fra una sessione e l'altra.

## Cos'è

Una pagina che cerca i prodotti suoi nei volantini dei supermercati vicini a
casa (Torino, corso Siracusa). Ogni prodotto è un bottone: lo tocchi ed escono
le offerte, dalla più conveniente in giù, col prezzo per unità. Chi non trova
quello che vuole lo accende da un catalogo di 67 voci diviso per reparto.

Pubblicata in due posti, **e vanno aggiornati tutti e due**:
- il sito, `https://manliograndi-del.github.io/spesa-a/` — un commit su `main`
- l'artifact, il link che ha anche sua moglie — `Artifact` con lo stesso URL

## Vincoli tecnici — non negoziabili senza chiederglielo

1. **I prezzi si leggono a occhio dalle pagine dei volantini.** L'OCR non legge
   le scritte grandi: serve a trovare la pagina, non il prezzo. I riassunti
   online sbagliano — tre errori trovati e documentati in NOTE.md.
2. **Non si pubblicano i PDF né le immagini dei volantini.** Solo collegamenti
   ai siti di chi li mette online.
3. **Mai scrivere il tag di chiusura dello script per esteso** dentro il codice
   della pagina, commenti compresi: spezza la pagina a metà, in silenzio.
4. **Nel CSS non esiste `prefers-color-scheme: dark`.** Il telefono di Manlio è
   in modalità notte e la pagina gli si apriva nera.
5. **Prima di rigenerare, si legge la lista viva dalla pagina pubblicata.** Se
   non si riesce a leggerla, ci si ferma senza pubblicare: rigenerare a vuoto
   cancella la lista di prodotti loro.
6. **A ogni rilascio si alza il numero di cache in `sw.js`** (`spesa-v29` →
   `spesa-v30`), se no resta in giro la copia vecchia.
7. Il progetto della palestra (`manliograndi-del/palestra`) **non si tocca**.

## Come si rifà

    export PYTHONPATH=<progetto>/strumenti
    python3 -m scarica <chiave>    # le pagine del volantino
    bash <progetto>/strumenti/leggi.sh    # OCR di ogni pagina
    python3 -m indice              # aggiorna indice.json
    python3 -m pagina              # le tre copie in out/
    python3 -m storia              # il diario delle novità del giorno
    python3 -m novita              # la pagina delle novità (tasto in alto a destra)
    python3 -m stampa              # il PDF del catalogo da stampare
    python3 -m lette               # quante pagine ho letto davvero
    bash <progetto>/strumenti/prove.sh    # TUTTE le prove
    python3 -m pulizia out/sito.html      # codice rimasto in giro

Poi `cp out/sito.html index.html`, `cp out/novita.html novita.html`,
`cp out/catalogo.pdf catalogo.pdf`, alza `sw.js`, commit, push, e ripubblica
l'artifact.

**`prove.sh` è il comando che conta.** Una pagina che non passa non si pubblica.
Serve `npm install` dentro il progetto.

## Come si leggono i volantini — la parte che ho sbagliato tre volte

**Si leggono per intero, pagina per pagina.** NON si interroga l'indice delle
parole per aprire solo le pagine che rispondono: così si trova soltanto quello
che si è già pensato di cercare. Le pizze, Mercatò e il pesce sono lo stesso
errore tre volte, e Manlio se n'è accorto tutte e tre da fuori.

- **Una categoria con zero o una sola offerta è quasi sempre un buco mio, non il
  mondo.** Se sei supermercati su sette non hanno la pizza, non è il mondo.
- **Prima i volantini che durano**, non i più trascurati: leggere 52 pagine di
  un volantino che scade fra quattro giorni è tempo buttato.
- **`python3 -m lette`** dice la copertura, e `lette <chiave>` elenca le pagine
  mai aperte. Al 2026-09-09: 160 pagine lette su 313. Mercatò, Carrefour Iper e
  il Bennet «Dolce Buongiorno» sono al 100%, letti per intero.
- **Cercare i volantini nuovi non è la stessa cosa che guardare le scadenze.**
  `pulisci.py` dice solo cosa sta scadendo di quello che hai già. Le insegne però
  pubblicano volantini che si sovrappongono: il Bennet «Dolce Buongiorno» è
  uscito il 3 settembre mentre il Bennet vecchio era ancora valido, e per sei
  giorni non l'ha visto nessuno. **A ogni giro guarda anche cosa è USCITO**, non
  solo cosa muore.
- Una pagina di quaderni, pubblicità o punti premio **si scarta**, e si scrive
  in `strumenti/scartate.py` col motivo, così non torna nell'elenco delle cose
  da fare. Regola sua: «una volta che l'hai vista, lasciala perdere».
  **Ma si scarta solo dopo averla APERTA**, mai dal titolo o dall'OCR: è così
  che mi ero perso una pagina intera di pescheria del Bennet.

## Trappole già pagate, che il programma adesso blocca da solo

`dati.py` si ferma con un errore se ne rifai una. Non toglierle.

- **Righe doppie** (stessa insegna, stesso prodotto, stesso formato): rileggendo
  un volantino ne ho riscritte dieci, e la stessa offerta compariva due volte.
- **Date ripetute dal volantino**: scrivere su una riga le stesse date del
  volantino che la contiene la fa passare per «offerta ristretta», e una
  ristretta non ancora cominciata **non si mostra affatto**. Mi ha reso
  invisibili 22 righe senza che niente lo segnalasse. Le date sulla riga
  servono solo al caso vero (la pagina «Weekend più uno» dell'MD).
- **Categorie fuori catalogo**: un prezzo in una categoria che non esiste
  verrebbe caricato e non mostrato a nessuno, in silenzio.

## Regole della pagina decise con lui

- **L'elenco è in ordine di prezzo e basta.** Niente eccezioni in fondo. Il
  bollino verde «il meno caro» va al meno caro **che vale oggi**, che può non
  essere la prima riga.
- **Ogni riga dice fino a quando vale.** I volantini durano periodi diversi.
- Le offerte scadute spariscono da sole: il giudizio lo dà il browser di chi
  guarda, con la sua data, non il programma che genera.
- **«Cerca fra i prezzi» cerca fra TUTTE le offerte, non nel catalogo.** È il
  tasto tratteggiato accanto a «+ altri prodotti», ed è un'altra cosa dalla
  casella dentro il cassetto: quella accende i prodotti della lista, questa
  trova una singola offerta fra tutte quelle lette (marca, formato, insegna,
  note). Chiesto il 2026-09-15: «trovare esattamente un singolo prodotto fra
  tutte le offerte». Due regole sue, da non cambiare:
  - **nei risultati NON c'è il bollino verde «il meno caro»**. Lì dentro il
    verde vorrebbe dire «il meno caro di quello che hai scritto», e uno
    leggerebbe «il meno caro della categoria»: una novità falsa.
  - **il pannello sta FUORI dalla `.barra`**, per la stessa ragione del
    cassetto: la barra è appiccicata in alto e se le cresce dentro qualcosa
    il telefono si blocca a ogni scorrimento.
  Cassetto e ricerca **non stanno aperti insieme**: aprirne uno chiude l'altro.
  - **il tasto è rosso pieno e su una riga tutta sua** (`.tasto.trova`), dal
    2026-09-15: tratteggiato e grigio come «+ altri prodotti» Manlio non lo
    vedeva. Rosso pieno **in mezzo alle pastiglie** non si poteva: lì il rosso
    pieno vuol dire «prodotto acceso». Da solo, largo quanto lo schermo, no.
    Il bottone **tiene anche la classe `agg`**: è con quella che tutte le
    prove riconoscono i bottoni che non sono prodotti della lista.
- **In fondo, ogni volantino dell'elenco ha due tasti** (chiesti il 2026-09-18):
  **«Le offerte (N)»** apre le offerte lette da quel volantino, divise per
  reparto, e **«Il volantino ↗»** apre la sua prima pagina sul sito di chi lo
  pubblica. Tutti e due in una **pagina nuova**, come ha chiesto lui. Regole da
  non cambiare: il numero sul tasto è quello che vale **oggi** (un volantino
  scaduto non ha il tasto, ha la scritta spenta «offerte scadute»); dentro
  quelle offerte **non c'è il bollino verde**, che lì vorrebbe dire «il meno
  caro di questo negozio» e si leggerebbe «di tutti»; il pannello è quello
  della ricerca, che sta **fuori dalla `.barra`**. La pagina nuova è la pagina
  stessa con `#volantino=...` in coda: non ci sono pagine generate in più.
- **La pagina Novità comincia dai volantini, non dai prezzi** (chiesto il
  2026-09-19): in cima il riquadro **«Volantini aggiornati»** (nuovi, riletti,
  finiti) sulla finestra scelta — i tasti sono **Oggi / 3 giorni / 7 giorni** —
  poi la **tabella di tutti i volantini** (in corso, in arrivo, appena finiti)
  e solo dopo il diario dei prezzi. I volantini che so in arrivo ma non ho
  ancora letto stanno in **`VOLANTINI_ATTESI`** in `dati.py` e in tabella sono
  segnati «prezzi non ancora letti»: si tolgono di lì appena il volantino
  entra in `VOLANTINI`. La prova è `prova-novita.js`.
- **Il tasto «Aiuto» sta in cima, accanto a «Novità»** (chiesto il 2026-09-21)
  e apre una finestra che spiega come si usa la pagina. **Non si apre mai da
  sola e si riapre sempre**: è il contrario della finestra «Cosa c'è di
  nuovo». Il tasto è **vuoto, non rosso pieno**: il rosso pieno qui vuol dire
  «premi qui adesso», e l'aiuto non lo è. **Il testo l'ha letto e approvato
  Manlio prima che lo mettessi**: se va cambiato, si rifà così. La prova è
  `prova-aiuto.js`.
- **La finestra «Cosa c'è di nuovo» si apre alla prima apertura** (chiesta il
  2026-09-18) e racconta **l'interfaccia, non i prezzi**: cosa si può fare
  adesso che prima non si poteva, a partire dalla casella di ricerca. I prezzi
  nuovi restano nel tasto «Novità» in alto a destra. **Dentro non ci vanno
  offerte né prezzi**, e la prova `prova-novita-pagina.js` se ne accorge. Le
  novità nuove si aggiungono in fondo a `NOVITA_PAGINA` in `pagina.py`, con la
  data davanti all'id: chi le ha già viste vedrà comparire **solo quella
  nuova**.
- **Una novità falsa è peggio di nessuna novità: manda uno in negozio.** Vale
  per il diario e per i prezzi: se un conto è ambiguo (peso sgocciolato, prezzo
  valido solo comprandone tre), si sceglie il numero che NON fa sembrare
  l'offerta più conveniente di quello che è, e lo si scrive nella nota.

## Dove va Manlio

**Mercatò di via Filadelfia 232**, insegna Mercatò semplice — confermato da lui
il 2026-09-05, non dedotto. A Torino ci sono anche Mercatò Local, Big ed Extra,
con volantini diversi: il più vicino a corso Siracusa è un Local, quindi la
distanza da sola avrebbe scelto il negozio sbagliato.

## Da fare adesso (aggiornato il 2026-09-22)

- **Letto per intero il 2026-09-22: Lidl dal 24 al 30 settembre** (`lidl24`,
  52 pagine, trovato già con le pagine pubblicate — annunciato il 21/9 ma
  ancora senza pagine vere, oggi c'erano). 93 prezzi nuovi in `dati.py`, in
  quasi tutti i reparti (macelleria, salumi, formaggi, pesce, surgelati,
  dispensa, bevande, casa, colazione, ortofrutta). 27 pagine scartate
  (abbigliamento e stivali bambini, attrezzi auto e fai-da-te Parkside,
  elettrodomestici SilverCrest, fiori e piante, viaggi Lidl, pubblicità varie):
  in `scartate.py`. Diverse offerte valgono solo **dal 24 al 27** o solo
  **dal 28 al 30**, non tutto il periodo: le date sono scritte riga per riga.
  `lidl17` e `lidlfv17` (17-23 settembre) restano validi altri due giorni,
  **nessun buco**. Copertura: 52/52 pagine lette.
- **CHIUSA: letto per intero il 2026-09-22 l'Ekom «I più ekonomici» (22
  settembre-5 ottobre)** (`ekom22`, 16 pagine). Non l'avevo trovato da solo —
  kimbino.it/ekom/ non lo sapeva ancora — **è stato Manlio a segnalare il
  link giusto**, `ekomdiscount.it/volantini`, il sito ufficiale. Da lì in poi
  la fonte per l'Ekom è quella, non più kimbino: in NOTE.md c'è scritto come
  leggerla (serve un browser vero, non un fetch semplice, ma le pagine si
  prendono con un `curl` normale una volta trovato l'indirizzo dell'API).
  102 prezzi nuovi in `dati.py`. 3 pagine scartate (copertina, concorso a
  premi, pubblicità app): in `scartate.py`. Alcune offerte valgono solo con
  la carta EKOM UP, segnato riga per riga come per la MD Buona Spesa Card.
  Copertura: 16/16 pagine lette.
- **Ipercoop: `promoipercoop.it` ancora 503**, controllato di nuovo il
  2026-09-22 (5° giorno di fila). Da riprovare.
- **Mercatò, Bennet, Eurospin, MD, Carrefour Iper: nessuna novità** il
  2026-09-22, controllati tutti sulla fonte (anteprimavolantino, kimbino).

- **Fatto il 2026-09-21 il tasto «Aiuto»** in cima accanto a «Novità», col
  testo approvato da Manlio prima di metterlo. Pubblicato su sito e artifact.

- **L'ora del controllo automatico è stata spostata alle 7 del mattino**
  (chiesto da Manlio il 2026-09-21). La Routine si chiama «Spesa — controllo
  giornaliero dei volantini» e adesso ha `0 5 * * *`: **il cron è in UTC**, e
  con l'ora legale (UTC+2) parte alle 7 italiane — nei fatti fra le 7:05 e le
  7:15, perché il servizio ha qualche minuto di ritardo. **Attenzione al
  25 ottobre 2026**: quel giorno torna l'ora solare (UTC+1) e `0 5 * * *`
  diventerebbe **le 6 del mattino**. Quel giorno, o subito dopo, va rimesso a
  `0 6 * * *` con `update_trigger`, se no il giro parte un'ora prima di quanto
  vuole lui. Stessa cosa al contrario l'ultima domenica di marzo.

- **Ekom «I più ekonomici» (22 settembre-5 ottobre): ancora non online, 3° giorno
  di fila che si controlla senza trovarlo** (19, 20, 21 settembre — kimbino
  invariato all'8-21, ekom.it ancora 503). `ekom08` scade oggi 21 settembre:
  da domani, finché non esce il successore, **non ci saranno offerte Ekom** in
  lista. Detto a Manlio. **Da fare: appena esce online si legge per intero;
  se lui manda le foto delle pagine di carta, si legge da quelle.**
- **Eurospin e MD: niente da fare.** `eurospin10` e `md08` sono scaduti il 20
  settembre ma i loro successori (`eurospin24`, `md22`) erano già dentro
  `dati.py` da prima: nessun buco, nessuna offerta persa. Restano in `dati.py`
  finché non si fa un giro di pulizia (le offerte scadute spariscono da sole
  dalla pagina, per data del browser di chi guarda: non è urgente toglierle).
- **Ipercoop: `promoipercoop.it` ancora 503**, controllato di nuovo il
  2026-09-21 (3° giorno di fila). Da riprovare.
- **Mercatò, Bennet, Carrefour Iper: nessuna novità** il 2026-09-21, controllati
  tutti sulla fonte.

- **CHIUSA: il volantino Ekom di carta era il successivo.** Il 2026-09-19
  Manlio ha fotografato una pagina «Surgelati» (filetti di merluzzo Alaska
  400 g a 1,99, tentacoli di totano gigante, minestrone 450 g a 0,79, patate
  stick, pizza formato pala, churros) che **non era nel volantino 8-21
  settembre** che avevo letto. Verificato che non fosse una differenza di
  regione (la pagina Surgelati dell'edizione Toscana è identica a quella
  generale) e che online non ci fosse altro: kimbino, volantinofacile,
  offertolino, promoqui, doveconviene e il sito Ekom avevano solo l'8-21.
  Poi lui ha fotografato la copertina: **«I PIÙ EKONOMICI», dal 22 settembre
  al 5 ottobre**. Quindi **l'Ekom stampa il volantino prima di pubblicarlo
  online**, e questo è il primo caso visto nel progetto: la fonte era giusta,
  era solo in ritardo. Messo in `VOLANTINI_ATTESI` con le sue date vere, così
  in tabella si vede «in arrivo, prezzi non ancora letti».
  **Da fare: appena esce online (kimbino, come per l'8-21) si legge per
  intero e si toglie da `VOLANTINI_ATTESI`.** Se il 22 non è ancora online,
  Manlio manda le foto delle pagine e si legge da quelle: i prezzi si leggono
  a occhio comunque, cambia solo che quelle righe non avranno il collegamento
  alla pagina del volantino. **Ricontrollato il 2026-09-20: ancora non
  online** (kimbino invariato all'8-21, sito ekom.it 503).

- **Rifatta il 2026-09-19 la pagina Novità**, come ha chiesto Manlio: prima i
  volantini aggiornati (con il tasto «3 giorni» nuovo), poi la tabella di
  tutti i volantini con le date di validità, poi le novità dei prezzi. Solo
  `novita.html` è cambiata: la pagina dei prezzi è rimasta identica, e
  l'artifact non è stato ripubblicato perché il suo tasto «Novità» punta già
  al sito.

- **Letto per intero il 2026-09-19: Bennet «Un mondo di bellezza», dal 17 al
  30 settembre** (`bennet1709`, 27 pagine). Non è solo bellezza: da pagina 18
  in poi c'era un bel po' di spesa vera — pasta, riso, formaggi, salumi,
  surgelati, vino, acqua, oltre a shampoo, saponi e dentifrici. Circa 87
  prezzi nuovi in `dati.py`. 14 pagine scartate (styling capelli, creme viso,
  depilazione, deodoranti, rasoi uomo, assorbenti, integratori, pubblicità):
  in `scartate.py`. Diverse offerte «shampoo O balsamo» hanno lo stesso
  prezzo per due formati diversi: il conto è sempre sul formato più piccolo,
  per non sembrare più conveniente di quanto sia — stessa regola delle pagine
  1+1 dell'Ekom.
- **Tolti il 2026-09-19 i tre volantini scaduti da tre giorni**: `mercato`,
  `bennet0903` e `lidl10` (già coperti senza buchi dai loro successori). 596
  righe di prezzo in meno da `dati.py`, le loro voci tolte anche da
  `scartate.py`.

- **Fatta il 2026-09-18 la finestra «Cosa c'è di nuovo»**, chiesta da Manlio:
  si apre da sola la prima volta e elenca le novità della pagina (casella di
  ricerca, Ekom, due tasti sui volantini). Chi l'ha già vista non la rivede;
  chi torna dopo una novità nuova vede solo quella.

- **Aggiunta l'insegna Ekom il 2026-09-18**, chiesta da Manlio. Volantino
  «1+1» dell'8-21 settembre (`ekom08`), letto per intero: 16 pagine, 138
  prezzi. **Scade il 21 settembre**: il successore (dal 22) su kimbino non
  c'era ancora il 18, **da cercare nei prossimi giorni**. La fonte è kimbino
  come per il Mercatò, quindi gli indirizzi delle pagine stanno uno per uno in
  `strumenti/pagine_ekom.py` e **vanno rifatti a ogni volantino nuovo**. A
  Torino ci sono più Ekom ma **il volantino è lo stesso per tutti** (l'unico
  diverso è quello della Toscana): niente da scegliere come col Mercatò.
  **Le pagine 1+1**: la riga dice nel formato che sono due confezioni
  («2 × 300 g (1+1)») e la nota dice quanto costa una confezione sola — in
  NOTE.md c'è il perché, non cambiarlo senza chiederglielo.

- **Fatti il 2026-09-18 i due tasti su ogni volantino in fondo alla pagina**,
  chiesti da Manlio: «Le offerte» e «Il volantino», tutti e due in una pagina
  nuova. Pubblicati sul sito e sull'artifact, `sw.js` a v38. In NOTE.md c'è il
  perché di ogni scelta; la prova nuova è `prova-volantini.js`, dentro
  `prove.sh`.

- **Il 2026-09-17 il ramo `main` era rimasto indietro di 36 commit**: le
  sessioni del 15 e 16 settembre avevano lavorato e pubblicato l'Artifact, ma
  avevano spinto (`git push`) su un ramo secondario invece che su `main`, e il
  sito pubblico (che legge da `main`) era rimasto fermo a `sw.js` v27 per
  giorni, senza il Mercatò 17-30, il Carrefour Iper, il Bennet e il Lidl.
  **Sistemato oggi** portando `main` avanti fino a quel lavoro (fast-forward,
  nessun commit perso) e verificato che il sito online lo mostri davvero. **Da
  qui in poi: dopo ogni `git push`, controllare che sia andato su `main` (non
  su un ramo con un altro nome) prima di dire che è pubblicato.**
- **Uscito e preso un volantino Lidl in più, non un successore**: uno
  speciale «Frutta e Verdura» di 7 pagine, `lidlfv17`, valido come il Lidl
  generale (17-23 settembre) ma con offerte sue, aggiuntive. Letto per intero:
  12 prezzi nuovi (mele, susine, cavoli, aglio, rape rosse, uva, cetrioli
  snack, limoni). Tre suoi prodotti (Pere Williams, Patate Selenella, Zucca
  Butternut, Uva di Mazzarrone, Carote del Fucino, Pesche) ripetevano
  identici, stesso prezzo, quelli già letti nel Lidl generale 17-23: non
  riscritti, sennò `dati.py` si ferma per riga doppia. Tre prodotti (Cetrioli
  lunghi, Mango, Fichi freschi) erano «al pezzo» senza un peso indicato:
  nessun prezzo per unità onesto da scrivere, lasciati fuori. Una pagina
  scartata (pubblicità del premio «Sicurezza Alimentare»), in `scartate.py`.
- **Letto per intero il 2026-09-18: MD nuovo, dal 22 settembre al 4 ottobre**
  (`md22`, 37 pagine). 131 prezzi nuovi, in quasi tutti i reparti (macelleria,
  gastronomia, freschi, surgelati, dispensa, bevande, casa, più uno speciale
  Sardegna e un weekend «Weekend più Uno» valido solo dal 2 al 5 ottobre — le
  date sono scritte sulle singole righe). Alcuni prezzi valgono solo con la
  MD Buona Spesa Card: scritto nella nota di ogni riga, col prezzo pieno
  accanto. 13 pagine scartate (accessori cucina, casalingo, cura persona,
  tessile, e-mobility, viaggi, una pagina ricetta): in `scartate.py`.
- **CHIUSA: trovato e letto per intero l'Eurospin dal 24 settembre al 4
  ottobre** (`eurospin24`, 22 pagine), il giorno stesso in cui scadeva
  `eurospin10`: colma da solo il buco di 4 giorni che era segnato qui.
  ~140 prezzi nuovi in `dati.py`. Gran parte delle pagine erano un concorso a
  tema Bluey (giocattoli, abbigliamento, viaggi): scartate le pagine non
  alimentari (16-21), tenuti i pochi alimentari Bluey (latte, succo, pasta,
  asciugatutto) che restavano offerte vere. Pagina 12 (Frutta e verdura più
  Pescheria) ha un elenco di punti vendita aderenti: Torino ne ha diversi,
  alcuni senza reparto pescheria — segnato nella nota delle righe di
  pescheria. Pagina 22, «Doppio weekend di follia», ha offerte ristrette a
  due fine settimana (25-27 settembre e 2-4 ottobre): date scritte riga per
  riga, come per il «Weekend più uno» dell'MD.
- **Carrefour Iper: nessuna novità.** Fermo a `carriper15` (fino al 28).
  **Ipercoop: il sito `promoipercoop.it` risponde ancora 503** (visto il
  2026-09-19 e di nuovo il 2026-09-20, due giorni di fila) — da riprovare.
  L'ultima cosa vista era ancora solo «Scegli tu Grandi Marche», sconti
  percentuali senza un prezzo di base, non utilizzabile.
- **`md08` è scaduto il 20 settembre e non ha ancora un successore in
  `dati.py` diverso da quello già dentro.** Il successore (`md22`, dal 22) è
  già dentro: **c'è solo un giorno di buco** (il 21), niente da fare finché
  non si avvicina.
- **Il Carrefour Iper (`carriper15`, 15-28 settembre) è a posto, non
  riaprire la questione.** L'ultima pagina del suo volantino elenca gli
  ipermercati in cui vale e Torino non c'è: il 2026-09-07 Manlio ha detto che
  è sbagliato fermarsi lì — «le offerte ci sono a Torino e valgono davvero».
  In NOTE.md c'è per esteso.
- **Copertura letta: tutti i volantini con prezzi in `dati.py` sono al 100%**
  (bennet10, lidl17, lidlfv17, eurospin10, eurospin24, md08, carriper15,
  mercato17, md22, ekom08, bennet1709, lidl24, ekom22).
- **Scadenze da tenere d'occhio nei prossimi giorni**: `md08`, `eurospin10` ed
  `ekom08` sono scaduti (20 e 21 settembre) ma i loro successori sono già
  dentro `dati.py`: da togliere con `pulisci --fai` appena il programma lo
  permette, non è urgente. `bennet10`, `lidl17` e `lidlfv17` scadono il 23
  (occhio: nel Lidl 17-23 la «Panetteria» vale solo dal 17 al 20, e alcune
  offerte «Il meglio del lunedì» valgono solo dal 21 al 23 — già segnato
  nelle note delle singole righe). `mercato17` e `bennet1709` scadono il 30,
  `lidl24` anche (occhio: alcune sue offerte valgono solo dal 24 al 27 o solo
  dal 28 al 30, non tutto il periodo — già segnato riga per riga). `md22`
  scade il 4 ottobre, `eurospin24` anche. `ekom22` scade il 5 ottobre. La
  pagina Oktoberfest del Bennet (pagine 20-21 di `bennet10`) scade il 4
  ottobre, non il 23 come il resto — occhio quando si ributta il volantino.
  Il weekend Eurospin 25-27 settembre e quello del 2-4 ottobre (vedi sopra)
  valgono solo quei giorni, non tutto il periodo di `eurospin24`.
- **Il giro automatico non funziona, e non è un mistero da risolvere leggendo
  il codice**: parte, lavora pochi minuti e non lascia traccia. In NOTE.md c'è
  quello che si sa e quello che non si sa, e perché a mano riesce. Finché non lo
  si vede arrivare in fondo più volte di fila, **i volantini si mettono a
  mano**. **Il 2026-09-10, il 2026-09-15, il 2026-09-16, il 2026-09-17, il
  2026-09-18, il 2026-09-19, il 2026-09-20, il 2026-09-21 e il 2026-09-22 la
  sessione da Routine è arrivata in fondo**: ha letto un volantino per intero
  (o più) e pubblicato — ma il 17 settembre si
  è scoperto che le pubblicazioni del 15 e del 16 non erano davvero arrivate
  al sito (vedi sopra): un «pubblicato» nel registro non basta, va controllato
  che sia finito su `main`. Dal 2026-09-18 in poi, dopo ogni push, verificato
  che `index.html` scaricato dal sito online combaci byte per byte col file
  appena pubblicato.
- **Il buco del diario è chiuso (2026-09-15), e `.gitignore` non si tocca.**
  `storia/stato.json` resta fuori dal repository — «le fotografie no, le
  differenze sì» — ma **non serve più che sopravviva**: se manca, `storia.py`
  **rifà la fotografia da git**, tirando fuori `strumenti/` dall'ultimo commit
  che ha toccato `dati.py` e leggendolo con il `fotografia()` di adesso. La
  fotografia è solo una lettura di `dati.py`, e `dati.py` nel repository c'è.
  In più `storia.py` **riempie i giorni rimasti indietro uno per uno**, con la
  loro data e col `dati.py` in vigore quel giorno: un giorno può avere novità
  vere **senza che nessuno tocchi i prezzi**, perché a mezzanotte un volantino
  scade e il più conveniente di quella categoria diventa un altro. Così sono
  stati recuperati i giorni dal 10 al 15 settembre, che erano vuoti.
  **Da qui in poi `python3 -m storia` va lanciato PRIMA di committare**: il
  confronto è fra l'ultimo commit e quello che c'è adesso nella cartella.
- **Manlio deve correggere a penna il catalogo** (`catalogo.pdf`, 67 voci): le
  sue correzioni vanno riportate in `strumenti/catalogo.py`. Se le manda,
  applicarle e rifare il PDF con `python3 -m stampa`.
- **Restano a lui**: reinstallare l'icona dal nuovo indirizzo e mandare il link
  alla moglie.

## File del progetto

- `index.html` — il sito pubblicato (generato, non si modifica a mano)
- `catalogo.pdf` — il foglio da stampare e correggere
- `indice.json` — le parole di ogni pagina di ogni volantino, committato
- `storia/` — il diario, un file per giorno
- `strumenti/` — catalogo, dati, pagina, storia, lette, scartate, stampa, prove
- `NOTE.md` — la storia lunga e il perché di ogni scelta
