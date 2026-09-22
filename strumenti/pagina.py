# -*- coding: utf-8 -*-
"""Genera la pagina web da pubblicare.

Prodotti e prezzi da dati.py, lista di partenza da lista.py.

Due scelte volute, chieste da Manlio il 2026-09-02 dopo aver provato la
prima versione:

1. TEMA CHIARO FISSO. Niente blocco `prefers-color-scheme: dark`: il suo
   telefono è in modalità notte e la pagina gli si apriva nera («così non
   si può vedere»). Sfondo bianco dichiarato esplicitamente, così tiene
   anche se chi ospita la pagina è scuro.
2. BOTTONI IN CIMA. I prodotti sono bottoni in testa alla pagina; toccarne
   uno riempie la lista qui sotto, già ordinata dal meno caro. Prima erano
   schede da aprire e chiudere una per una, e per arrivare al tonno
   toccava scorrere.

La lista vive in localStorage, non sul server: vedi NOTE.md.
"""
import json, os
from dati import OFFERTE, VOLANTINI, UNITA, D
from catalogo import CATALOGO, REPARTI
from lista import PARTENZA

PDF     = {v.chiave: v.pdf for v in VOLANTINI}
MODELLO = {v.chiave: v.indirizzo for v in VOLANTINI}
ELENCO  = {v.chiave: v.pagine for v in VOLANTINI if v.pagine}

def indirizzo(chiave, n):
    """L'indirizzo pubblico di una pagina del volantino, per renderla cliccabile.
    Senza numero di pagina non c'e niente da aprire: torna None e la riga resta
    scritta e basta.

    Due forme, non una: quasi tutti i volantini hanno un indirizzo a schema col
    numero dentro; Mercato ha invece l'elenco delle pagine, una per una, perche
    la sua fonte le firma e il numero da solo non basta (vedi pagine_mercato)."""
    if not n:
        return None
    if chiave in ELENCO:
        elenco = ELENCO[chiave]
        return elenco[n - 1] if 1 <= n <= len(elenco) else None
    if chiave not in MODELLO or not MODELLO[chiave]:
        return None
    return MODELLO[chiave].format(n=n)
PERIODO = {v.chiave: v.periodo for v in VOLANTINI}

import datetime as _dt
_oggi = _dt.date.today()

# SCADUTO E «NON ANCORA COMINCIATO» LI DECIDE LA PAGINA, NON QUESTO PROGRAMMA.
# Qui si scrivono solo le due date; il confronto con oggi lo fa il browser di
# chi apre. Se lo facessimo qui, il giudizio resterebbe congelato al giorno in
# cui la pagina e stata generata: il 7 settembre avrebbe continuato a dare per
# buone offerte scadute il 6, finche qualcuno non rigenerava. E chi rigenera,
# per ora, non e affidabile — vedi il controllo giornaliero.

INIZIO = {v.chiave: v.inizio for v in VOLANTINI}
FINO   = {v.chiave: v.fino for v in VOLANTINI}

# Le date di un'offerta sono quelle del suo volantino, a meno che l'offerta ne
# abbia di sue e più strette: allora comandano quelle, e la riga viene marcata
# «ristretta» — la pagina la mostra soltanto nei giorni in cui vale davvero.
offerte = [dict(cat=o.cat, ins=o.ins, rep=o.rep, pro=o.pro, fmt=o.fmt, prezzo=o.prezzo,
                unitario=round(o.prezzo / o.qta, 3), pag=o.pag, pdf=PDF[o.chiave],
                url=indirizzo(o.chiave, o.pag),
                periodo=PERIODO[o.chiave], dubbio=(o.fonte == D), note=o.note,
                inizio=o.inizio or INIZIO[o.chiave],
                fino=o.fino or FINO[o.chiave],
                ristretta=bool(o.inizio or o.fino))
           for o in OFFERTE]

# indice.json sta nel progetto, non nella cartella di lavoro: le immagini dei
# volantini non si tengono (non sono nostre) e prima l'elenco delle pagine
# veniva filtrato guardando i file jpg sul disco. Risultato: chi rigenerava la
# pagina senza aver riscaricato tutto si ritrovava zero pagine. L'indice
# contiene già solo pagine esistite davvero: basta lui.
QUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ind = 'indice.json' if os.path.exists('indice.json') else os.path.join(QUI, 'indice.json')
idx = json.load(open(_ind, encoding='utf-8'))
idx = [r for r in idx if r['chiave'] in PDF]      # via i volantini tolti da dati.py
if not idx:
    raise SystemExit('indice.json vuoto o senza volantini noti: fermati.')
pagine = sorted((dict(ins=r['insegna'], periodo=r['validita'], pdf=PDF.get(r['chiave'], ''),
                      pag=r['pagina'], parole=r['parole'],
                      url=indirizzo(r['chiave'], r['pagina']))
                 for r in idx),
                key=lambda r: (r['ins'], r['periodo'], r['pag']))

MESI = ('gennaio febbraio marzo aprile maggio giugno luglio agosto '
        'settembre ottobre novembre dicembre').split()
# La data in fondo alla pagina si calcola: scritta a mano era rimasta indietro
# di due giorni e Manlio l'ha fotografata mentre si contraddiceva da sola.
OGGI = f'{_oggi.day} {MESI[_oggi.month - 1]} {_oggi.year}'
# Il primo indirizzo utile di ogni volantino: e quello che apre il tasto «Il
# volantino» in fondo alla pagina. Si prende dall'indice, cioe da pagine che
# esistono davvero, e non dal modello con dentro il numero: cosi il tasto non
# porta mai su un indirizzo inventato.
PRIMA = {}
for _r in pagine:
    if _r['url'] and _r['pdf'] not in PRIMA:
        PRIMA[_r['pdf']] = _r['url']

volantini = [x for x in (dict(ins=v.insegna, periodo=v.periodo, pdf=v.pdf,
                              pagine=len([y for y in pagine if y['pdf'] == v.pdf]),
                              apri=PRIMA.get(v.pdf),
                              inizio=v.inizio, fino=v.fino)
                         for v in VOLANTINI) if x['pagine']]

partenza = [dict(nome=n, parole=p, cat=c) for n, p, c in PARTENZA]

# LA LISTA CHE COMANDA E QUELLA CHE HANNO LORO.
# Manlio e la moglie aggiungono e tolgono prodotti dalla pagina pubblicata. Se
# l'aggiornamento settimanale dei volantini ripartisse da PARTENZA, gliela
# cancellerebbe tutta a ogni giro. Quindi: prima di rigenerare, si legge la
# lista dalla pagina viva (lista_attuale.py la tira fuori e la scrive qui) e si
# riparte da quella. PARTENZA serve solo se il file non c'e, cioe la prima volta.
lista_viva = 'lista-attuale.json'
if os.path.exists(lista_viva):
    salvata = json.load(open(lista_viva, encoding='utf-8'))
    if isinstance(salvata, list) and salvata:
        partenza = salvata
        print(f'lista ripresa dalla pagina viva: {len(partenza)} prodotti')

# Il catalogo va nella pagina perché è quello che si vede nel cassetto: nome,
# reparto e parole con cui il volantino chiama la stessa cosa. Sono ~66 voci,
# meno di 6 KB: non è quello che pesa.
catalogo = [dict(nome=v['nome'], rep=v['reparto'], parole=v['parole']) for v in CATALOGO]

# LE NOVITÀ DELLA PAGINA — non dei prezzi.
# Chiesto da Manlio il 2026-09-18: «la prima volta che uno apre la pagina
# sarebbe carino che ci fosse una finestra novità, a partire dalla casella di
# ricerca; le novità sono nell'interfaccia e nelle possibilità, non nei
# prodotti». Le novità dei PREZZI hanno gia il loro posto: il tasto «Novità»
# in alto a destra, che porta al diario. Qui dentro non ci vanno prezzi, ne
# offerte, ne nomi di prodotto: solo cosa si puo fare adesso che prima non si
# poteva.
#
# In ordine di tempo, dalla piu vecchia: si legge come una storia di cosa e
# arrivato. Aggiungendone una nuova si mette IN FONDO, con la sua data: chi ha
# gia visto le altre si vede comparire solo quella (il confronto e sull'id
# dell'ultima vista, tenuto nel browser di chi guarda).
NOVITA_PAGINA = [
    dict(id='2026-09-15-cerca', quando='15 settembre',
         titolo='«Cerca fra i prezzi»',
         testo='Il tasto rosso sotto i prodotti apre una casella che cerca fra '
               'TUTTE le offerte lette, non nel catalogo: scrivi una marca, un '
               'formato o il nome di un negozio e trovi quella singola offerta. '
               'È un\'altra cosa dalla casella dentro «+ altri prodotti», che '
               'invece accende i prodotti della lista.'),
    dict(id='2026-09-18-ekom', quando='18 settembre',
         titolo='Un supermercato in più: l\'Ekom',
         testo='I volantini letti adesso sono otto insegne invece di sette. '
               'Non devi fare niente: le offerte dell\'Ekom entrano da sole nel '
               'confronto di ogni prodotto che hai acceso.'),
    dict(id='2026-09-18-tasti', quando='18 settembre',
         titolo='Due tasti su ogni volantino',
         testo='In fondo alla pagina, nell\'elenco dei volantini, ogni riga ha '
               'due tasti: «Le offerte» ti mostra i prezzi letti da quel '
               'volantino, reparto per reparto, e «Il volantino» apre le sue '
               'pagine sul sito di chi lo pubblica. Tutti e due si aprono in '
               'una pagina nuova, così non perdi quello che stavi guardando.'),
]

DATI = json.dumps(dict(offerte=offerte, pagine=pagine, volantini=volantini,
                       catalogo=catalogo,
                       reparti=[r for r, _ in REPARTI],
                       unita={k: v[0] for k, v in UNITA.items()},
                       novita=NOVITA_PAGINA,
                       letto=OGGI),
                  ensure_ascii=False, separators=(',', ':'))
LISTA0 = json.dumps(partenza, ensure_ascii=False, separators=(',', ':'))

HTML = r'''<title>Spesa</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Asap:wght@400;500;600;700&family=Oswald:wght@500;600;700&display=swap">
<style>
/* Tema chiaro unico e dichiarato: nessun blocco scuro, perché la pagina
   si apriva nera sul telefono di Manlio in modalità notte. */
:root{
  --carta:#FFFFFF;
  --pannello:#F6F5F2;
  --inchiostro:#1B1B1A;
  --tenue:#6E6C66;
  --linea:#E5E3DD;
  --linea-forte:#CFCCC4;
  --rosso:#D40D2B;
  --su-rosso:#FFFFFF;
  --verde:#1E7A4B;
  --verde-tenue:#E6F3EC;
  --ambra:#8A5A08;
  --ambra-tenue:#FCF2DE;
  --f-testo:'Asap',ui-sans-serif,system-ui,'Segoe UI',sans-serif;
  --f-prezzo:'Oswald','Arial Narrow',ui-sans-serif,sans-serif;
  color-scheme:light;
}
*{box-sizing:border-box}
html{background:var(--carta)}
body{background:var(--carta);color:var(--inchiostro);font-family:var(--f-testo);
  font-size:16px;line-height:1.45;-webkit-text-size-adjust:100%}
button{font-family:var(--f-testo);color:inherit}
:focus-visible{outline:3px solid var(--rosso);outline-offset:2px}
.guscio{max-width:800px;margin:0 auto;padding:0 15px 60px}

/* ---- testa ---- */
header{padding:20px 0 2px}
h1{font-family:var(--f-prezzo);font-weight:700;font-size:26px;letter-spacing:.01em;
  line-height:1.05;margin:0;text-transform:uppercase}
/* La riga in alto: il luogo con accanto il bollino, e a destra le novità.
   Il bollino stava attaccato al titolo grande e andava a capo da solo, su una
   riga tutta sua: Manlio l'ha visto e ha chiesto di alzarlo. Qui la riga è
   corta e ci sta. */
.riga-alta{display:flex;align-items:center;justify-content:space-between;gap:10px;
  flex-wrap:wrap;margin-bottom:6px}
.dove{color:var(--rosso);font-size:12px;letter-spacing:.16em;text-transform:uppercase;
  font-weight:600;margin:0;display:flex;align-items:center;gap:8px}
.sottotitolo{color:var(--tenue);margin:8px 0 0;font-size:14px;max-width:62ch}
/* Il tasto «Novità», in alto a destra. Punta all'INDIRIZZO COMPLETO e non a
   «./novita.html»: la copia di Claude non ha una cartella accanto a se, e un
   collegamento relativo di la porterebbe nel vuoto. Si apre in una finestra
   nuova cosi non si perde il posto nell'elenco dei prezzi. */
.novita{flex:none;display:inline-flex;align-items:center;gap:6px;
  background:var(--rosso);color:var(--su-rosso);text-decoration:none;
  border-radius:99px;padding:9px 15px;font-size:14px;font-weight:700;
  letter-spacing:.02em;min-height:40px;line-height:1;white-space:nowrap}
.novita::after{content:'\2197';font-weight:600}
/* «Aiuto», chiesto da Manlio il 2026-09-21: un pulsantino accanto a «Novità».
   Vuoto invece che rosso pieno: il rosso pieno, in questa pagina, vuol dire
   «premi qui adesso» (il tasto Novità e «Cerca fra i prezzi»), e l'aiuto non
   e una cosa da premere adesso — e li per quando serve. */
.tasti-alti{flex:none;display:inline-flex;align-items:center;gap:8px}
.aiuto{background:var(--carta);border:1.5px solid var(--rosso);color:var(--rosso);
  border-radius:99px;padding:9px 15px;font-size:14px;font-weight:700;letter-spacing:.02em;
  min-height:40px;line-height:1;cursor:pointer;white-space:nowrap}

/* ---- barra dei prodotti ---- */
.barra{position:sticky;top:0;z-index:20;background:var(--carta);
  padding:12px 0 12px;border-bottom:2px solid var(--inchiostro);margin-top:14px}
.tasti{display:flex;flex-wrap:wrap;gap:8px}
.tasto{background:var(--carta);border:1.5px solid var(--linea-forte);border-radius:99px;
  padding:10px 15px;font-size:15px;font-weight:600;cursor:pointer;line-height:1.1;
  min-height:44px;white-space:nowrap}
.tasto[aria-pressed="true"]{background:var(--rosso);border-color:var(--rosso);color:var(--su-rosso)}
.tasto.agg{border-style:dashed;color:var(--tenue);font-weight:500}
/* «Cerca fra i prezzi». Era un bottone tratteggiato come «+ altri prodotti» e
   Manlio non lo vedeva: «poco visibile, dovrebbe essere rosso». Rosso pieno
   come chiede lui, ma su UNA RIGA TUTTA SUA (flex-basis 100%) e non in mezzo
   alle pastiglie dei prodotti: li dentro il rosso pieno vuol dire «prodotto
   acceso», e un rosso pieno in fila con quelli si leggerebbe come una voce
   della lista accesa per sbaglio. Da solo, largo quanto lo schermo, il rosso
   torna a voler dire quello che deve: «premi qui». */
.tasto.trova{flex:0 0 100%;background:var(--rosso);
  border-color:var(--rosso);color:var(--su-rosso);border-style:solid;
  font-weight:700;font-size:16px;min-height:48px;margin-top:2px}

/* ---- aggiunta ---- */
.cassetto[hidden]{display:none}
.cassetto{margin-top:14px;background:var(--pannello);border:1.5px solid var(--linea);
  border-radius:12px;padding:12px}
.cerca{width:100%;border:1.5px solid var(--linea-forte);border-radius:10px;
  padding:12px 13px;font-size:16px;background:var(--carta);color:var(--inchiostro);
  font-family:var(--f-testo)}
.cerca:focus{outline:none;border-color:var(--rosso)}
.reparto{font-family:var(--f-prezzo);text-transform:uppercase;letter-spacing:.08em;
  font-size:11.5px;font-weight:600;color:var(--tenue);margin:16px 0 8px}
.reparto:first-child{margin-top:14px}
.chiudi{width:100%;margin-top:16px;background:var(--inchiostro);color:var(--carta);border:0;
  border-radius:10px;padding:13px;font-size:15px;font-weight:600;cursor:pointer;min-height:48px}
.fuori-catalogo{margin:8px 0 0;font-size:13.5px;color:var(--tenue)}
.form-agg{display:flex;gap:8px;margin-top:16px}
.form-agg input{flex:1;min-width:0;background:var(--carta);color:var(--inchiostro);
  border:1.5px solid var(--rosso);border-radius:10px;padding:12px 13px;
  font-family:var(--f-testo);font-size:16px}
.form-agg input:focus{outline:none}
.form-agg button{background:var(--rosso);color:var(--su-rosso);border:0;border-radius:10px;
  padding:0 18px;font-size:15px;font-weight:600;cursor:pointer;min-height:46px}

/* ---- la casella che cerca fra TUTTI i prezzi ---- */
/* Sta fuori dalla barra appiccicata, come il cassetto e per la stessa ragione:
   dentro, la barra diventerebbe piu alta dello schermo e il telefono dovrebbe
   rifarne i conti a ogni tocco. */
.ricerca[hidden]{display:none}
.ricerca{margin-top:14px;background:var(--pannello);border:1.5px solid var(--linea);
  border-radius:12px;padding:12px}
.ricerca .q{width:100%;border:1.5px solid var(--rosso);border-radius:10px;
  padding:13px 13px;font-size:16px;background:var(--carta);color:var(--inchiostro);
  font-family:var(--f-testo)}
.ricerca .q:focus{outline:none}
.quanti-trovati{margin:10px 0 0;font-size:13.5px;color:var(--tenue)}
.quanti-trovati b{color:var(--inchiostro)}
#trovati{margin-top:4px}
#trovati .fascia:first-child{margin-top:14px}

/* ---- intestazione del risultato ---- */
.capo{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:20px 0 2px}
.capo .info{flex:none}
/* Dice cosa fa, invece di una crocetta da interpretare. */
.elimina{flex:none;background:var(--carta);border:1.5px solid var(--rosso);color:var(--rosso);
  border-radius:99px;padding:8px 15px;font-size:14px;font-weight:600;cursor:pointer;
  min-height:38px;line-height:1.1;white-space:nowrap}
.conferma[hidden]{display:none}
.conferma{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin-top:10px;
  background:#FBEEF0;border:1.5px solid var(--rosso);border-radius:10px;padding:10px 12px}
.conferma span{font-size:14.5px;font-weight:600;flex:1;min-width:9em}
.conferma button{border-radius:9px;padding:9px 15px;font-size:14.5px;font-weight:600;
  cursor:pointer;min-height:42px;border:1.5px solid var(--rosso);background:var(--carta);
  color:var(--rosso)}
.conferma .si{background:var(--rosso);color:var(--su-rosso)}
.capo h2{font-family:var(--f-prezzo);text-transform:uppercase;letter-spacing:.02em;
  font-size:22px;font-weight:600;margin:0}
#risultato .quanti{color:var(--tenue);font-size:13px;font-variant-numeric:tabular-nums;
  margin:0 0 8px}
.sinonimi{margin:6px 0 0;font-size:13.5px;color:var(--tenue);display:flex;
  flex-wrap:wrap;gap:6px;align-items:baseline}
.sinonimi em{font-style:normal;background:var(--pannello);border:1px solid var(--linea);
  border-radius:99px;padding:2px 9px;font-size:13px;color:var(--inchiostro)}
.gestisci{display:flex;gap:9px;margin:12px 0 0;flex-wrap:wrap}
.gestisci button{background:var(--carta);border:1.5px solid var(--linea-forte);border-radius:9px;
  padding:10px 16px;font-size:14.5px;font-weight:600;cursor:pointer;min-height:44px}
.form-rin{display:none;gap:8px;margin-top:10px}
.form-rin.on{display:flex}
.form-rin input{flex:1;min-width:0;border:1.5px solid var(--rosso);border-radius:10px;
  padding:12px 13px;font-family:var(--f-testo);font-size:16px;background:var(--carta);
  color:var(--inchiostro)}
.form-rin input:focus{outline:none}
.form-rin button{background:var(--rosso);color:var(--su-rosso);border:0;border-radius:10px;
  padding:0 18px;font-size:15px;font-weight:600;cursor:pointer;min-height:46px}

/* ---- elenco prezzi ---- */
.fascia{font-family:var(--f-prezzo);text-transform:uppercase;letter-spacing:.06em;
  font-size:12.5px;font-weight:600;color:var(--tenue);margin:22px 0 0}
.prezzo-riga{display:grid;grid-template-columns:1fr auto;gap:3px 14px;
  padding:13px 0;border-top:1px solid var(--linea)}
.prezzo-riga:first-of-type{border-top:1.5px solid var(--inchiostro)}
.prezzo-riga .nome{margin:0;font-size:16.5px;font-weight:600;line-height:1.25}
.prezzo-riga .sotto{margin:3px 0 0;color:var(--tenue);font-size:13.5px}
.prezzo-riga .sotto b{color:var(--inchiostro);font-weight:600}
.prezzo-riga .val{grid-row:1/3;text-align:right;font-family:var(--f-prezzo);
  font-variant-numeric:tabular-nums;line-height:1;white-space:nowrap}
.prezzo-riga .val .n{display:block;font-size:27px;font-weight:700;color:var(--rosso)}
.prezzo-riga .val .u{display:block;font-family:var(--f-testo);font-size:10.5px;
  letter-spacing:.08em;text-transform:uppercase;color:var(--tenue);margin-top:4px}
.prezzo-riga .coda{grid-column:1/-1;margin:7px 0 0;display:flex;flex-wrap:wrap;gap:6px;
  align-items:center}
.bollo{font-size:11.5px;letter-spacing:.05em;text-transform:uppercase;font-weight:700;
  border-radius:5px;padding:3px 8px}
.bollo.meno{background:var(--verde-tenue);color:var(--verde)}
.bollo.dubbio{background:var(--ambra-tenue);color:var(--ambra)}
.bollo.dopo{background:#E9EEF6;color:#2B4A7A}
.bollo.stretta{background:var(--rosso);color:var(--su-rosso)}
.prezzo-riga .sotto .quando{white-space:nowrap}
.prezzo-riga .sotto .quando.stretta{color:var(--rosso);font-weight:700}
.prezzo-riga .nota{grid-column:1/-1;margin:6px 0 0;font-size:13.5px;color:var(--tenue)}
.prezzo-riga .dove{grid-column:1/-1;margin:6px 0 0;font-size:13px;color:var(--tenue);
  border-left:3px solid var(--linea);padding-left:9px}
a.dove.apri{display:inline-block;margin-top:8px;color:var(--rosso);font-weight:600;
  text-decoration:underline;text-underline-offset:3px;border-left:0;padding:7px 0;
  min-height:34px}
a.dove.apri::after{content:' \2197'}

/* ---- elenco pagine ---- */
.pag-riga{display:flex;justify-content:space-between;align-items:baseline;gap:12px;
  padding:11px 0;border-top:1px solid var(--linea);font-size:14.5px}
.pag-riga:first-of-type{border-top:1.5px solid var(--inchiostro)}
.pag-riga .ins{font-weight:600}
.pag-riga .per{display:block;color:var(--tenue);font-size:12.5px;font-weight:400}
.pag-riga .np{font-family:var(--f-prezzo);font-size:19px;font-weight:600;
  font-variant-numeric:tabular-nums;white-space:nowrap}
a.pag-riga{text-decoration:none;color:inherit}
a.pag-riga.apribile{padding:13px 0;min-height:48px}
a.pag-riga.apribile .ins{color:var(--rosso);text-decoration:underline;text-underline-offset:3px}
a.pag-riga.apribile .np{color:var(--rosso)}
a.pag-riga.apribile .np::after{content:' \2197';font-family:var(--f-testo);font-size:13px}
.altre{width:100%;margin-top:12px;background:var(--pannello);border:1.5px solid var(--linea);
  border-radius:10px;padding:12px;font-size:14.5px;font-weight:600;cursor:pointer;min-height:46px}
.vuoto{color:var(--tenue);font-size:14.5px;margin:14px 0 0;background:var(--pannello);
  border-radius:10px;padding:14px}

/* ---- coda ---- */
.spiega{margin-top:34px;background:var(--pannello);border-radius:12px;padding:16px 16px 4px}
.spiega h2{font-family:var(--f-prezzo);text-transform:uppercase;font-size:15px;
  letter-spacing:.04em;margin:0;display:flex;align-items:center;gap:9px}
/* Il bollino «i». Manlio: «la pagina è molto lunga, le spiegazioni meglio che
   appaiano solo quando si fa clic su un bollino di informazioni». Tondo, con
   la i minuscola, grande abbastanza da prendersi col dito. */
.info{flex:none;width:24px;height:24px;border-radius:50%;border:1.5px solid var(--linea-forte);
  background:var(--carta);color:var(--tenue);font-family:var(--f-testo);font-size:14px;
  font-weight:700;line-height:1;cursor:pointer;padding:0;display:grid;place-items:center}
.info:hover{border-color:var(--rosso);color:var(--rosso)}
.info[aria-expanded="true"]{background:var(--rosso);border-color:var(--rosso);color:var(--su-rosso)}
.dettaglio[hidden]{display:none}
.dettaglio{margin-top:10px}
.spiega .dettaglio > p:last-child{margin-bottom:12px}
.spiega > h2 + .dettaglio{margin-bottom:0}
.spiega > h2:not(:first-child){margin-top:18px}
.spiega p{font-size:14px;margin:0 0 12px}
.spiega .ev{color:var(--ambra);font-weight:700}
/* ---- la finestra delle novità della pagina ---- */
/* Sta SOPRA tutto (la barra appiccicata ha z-index 20) e si chiude in tre
   modi: il tasto, il buio intorno, il tasto Esc. Si apre una volta sola:
   quello che uno ha gia visto se lo ricorda il suo browser. */
.buio[hidden]{display:none}
.buio{position:fixed;inset:0;z-index:60;background:rgba(20,19,18,.5);
  display:flex;align-items:center;justify-content:center;padding:16px}
.finestra{background:var(--carta);border-radius:14px;max-width:460px;width:100%;
  max-height:84vh;overflow:auto;padding:18px 18px 0;
  box-shadow:0 18px 50px rgba(0,0,0,.28)}
/* Il tasto per chiudere resta SEMPRE in fondo allo schermo, attaccato: con le
   novità lunghe finiva sotto il bordo e per chiuderla bisognava indovinare
   che si poteva scorrere dentro la finestra. Una finestra che non si capisce
   come si chiude e una trappola. */
.pie-finestra{position:sticky;bottom:0;background:var(--carta);padding:4px 0 14px}
.finestra h2{font-family:var(--f-prezzo);text-transform:uppercase;font-size:17px;
  letter-spacing:.03em;margin:0 0 4px}
.finestra .sotto-titolo{margin:0 0 14px;color:var(--tenue);font-size:13.5px}
.finestra .voce{border-top:1px solid var(--linea);padding:13px 0}
.finestra .voce:first-of-type{border-top:1.5px solid var(--inchiostro)}
.finestra .quando{display:block;color:var(--tenue);font-size:11.5px;
  letter-spacing:.06em;text-transform:uppercase;font-weight:700;margin-bottom:3px}
.finestra .voce h3{margin:0 0 4px;font-size:16px}
.finestra .voce p{margin:0;font-size:14px;color:var(--inchiostro)}
.vol{list-style:none;padding:0;margin:10px 0 0;display:grid;gap:1px;background:var(--linea);
  border:1px solid var(--linea);border-radius:10px;overflow:hidden}
.vol li{background:var(--carta);padding:11px 13px;font-size:14px}
.vol .capo-vol{display:flex;justify-content:space-between;align-items:baseline;gap:12px}
/* I DUE TASTI DI OGNI VOLANTINO, chiesti da Manlio il 2026-09-18: uno apre i
   prezzi letti da quel volantino, l'altro il volantino stesso sul sito di chi
   lo pubblica. Larghi uguali, uno accanto all'altro, alti abbastanza da
   prendersi col dito sul telefono. */
.vol-tasti{display:flex;gap:8px;margin-top:9px}
.vol-t{flex:1 1 0;min-height:40px;display:flex;align-items:center;justify-content:center;
  gap:3px;text-align:center;padding:8px 10px;border:1.5px solid var(--linea-forte);
  border-radius:9px;background:var(--pannello);color:var(--rosso);font-weight:600;
  font-size:13.5px;font-family:inherit;text-decoration:none;cursor:pointer}
.vol-t.fuori::after{content:'\2197'}
.vol-t.spento{color:var(--tenue);border-style:dashed;cursor:default;font-weight:400}
.vol .i{font-weight:600}
.vol .p{color:var(--tenue);font-size:13px}
.vol .n{color:var(--tenue);font-size:12.5px;font-variant-numeric:tabular-nums;white-space:nowrap}
footer{margin-top:28px;padding-top:14px;border-top:1px solid var(--linea);
  color:var(--tenue);font-size:13px}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>

<div class="guscio">
<header>
  <div class="riga-alta">
    <p class="dove">Torino · Corso Siracusa
      <button type="button" class="info" aria-expanded="false"
              aria-label="Come funziona questa pagina">i</button></p>
    <span class="tasti-alti">
      <button type="button" class="aiuto" id="apri-aiuto">Aiuto</button>
      <a class="novita" href="https://manliograndi-del.github.io/spesa-a/novita.html"
         target="_blank" rel="noopener noreferrer">Novità</a>
    </span>
  </div>
  <h1>La lista della spesa</h1>
  <div class="dettaglio" id="dett-testa" hidden>
    <p class="sottotitolo">Tocca un prodotto: qui sotto compaiono le offerte, dalla più
    conveniente in giù. Con «+ altri prodotti» scegli i tuoi dal catalogo.
    Volantini di Mercatò, Lidl, Eurospin, MD, Bennet, Ekom, Ipercoop e Carrefour Iper.</p>
    <p class="sottotitolo" id="dove-vive"></p>
  </div>
</header>

<div class="barra">
  <div class="tasti" id="tasti" role="group" aria-label="Scegli il prodotto"></div>
  <p class="stato" id="stato-lista" role="status"></p>
</div>

<!-- IL CASSETTO STA FUORI DALLA BARRA, E NON È UN DETTAGLIO.
     Stava dentro, e la barra è appiccicata in alto: aprendolo, quella barra
     diventava più alta dello schermo e il telefono doveva ricalcolarla a ogni
     tocco e a ogni scorrimento. Manlio: «escono solo le prime categorie, poi
     la pagina resta bloccata per un tempo abbastanza lungo». Qui fuori la
     barra resta piccola e il cassetto è roba normale che scorre. -->
<div class="cassetto" id="cassetto" hidden>
  <input class="cerca" id="cerca" type="text" placeholder="Cerca un prodotto…"
         autocomplete="off" aria-label="Cerca un prodotto nel catalogo">
  <div id="scaffali"></div>
  <form class="form-agg" id="form-agg">
    <input id="nuovo" type="text" placeholder="Un altro nome, o più separati da virgola"
           autocomplete="off" aria-label="Nomi del prodotto da aggiungere, separati da virgola">
    <button type="submit">Aggiungi</button>
  </form>
  <p class="fuori-catalogo" id="fuori-catalogo"></p>
  <button type="button" class="chiudi" id="chiudi-cassetto">Fatto</button>
</div>

<!-- LA RICERCA STA FUORI DALLA BARRA, come il cassetto. -->
<div class="ricerca" id="ricerca" hidden>
  <input class="q" id="q" type="search" placeholder="Scrivi un prodotto, una marca, un negozio…"
         autocomplete="off" aria-label="Cerca fra tutti i prezzi dei volantini">
  <p class="quanti-trovati" id="quanti-trovati" role="status"></p>
  <div id="trovati"></div>
  <button type="button" class="chiudi" id="chiudi-ricerca">Fatto</button>
</div>

<div id="risultato"></div>


<section class="spiega">
  <h2>Come leggerla <button type="button" class="info" aria-expanded="false" aria-label="Mostra la spiegazione">i</button></h2>
  <div class="dettaglio" hidden>
  <p>In cima ci sono <b>i prodotti che hai scelto tu</b>. Per cambiarli tocca
  <b>«+ altri prodotti»</b>: si apre un cassetto con tutto il catalogo, diviso per reparto come
  il negozio. Tocca un prodotto per accenderlo, toccalo di nuovo per spegnerlo, poi «Fatto».
  <b>Nessuno deve chiedere niente a nessuno</b>: ognuno accende i suoi, sul suo telefono.</p>
  <p>Nel cassetto c'è anche <b>una casella per cercare</b>, e cerca anche fra i nomi che usa il
  volantino: scrivendo «bovino» trovi la carne di bue, scrivendo «lavatrice» trovi il
  detersivo.</p>
  <p>I prezzi sono <b>letti a mano</b>, uno per uno, dalle pagine dei volantini. Il confronto è
  per unità e cambia col prodotto: la carne al chilo, il latte al litro, le uova all'uovo, la
  carta igienica al rotolo, il detersivo a lavaggio. Al chilo il detersivo darebbe un numero
  vero e inutile.</p>
  <p><b>Non tutte le voci del catalogo hanno già i prezzi.</b> Quelle che non ce l'hanno ancora
  ti dicono in quali pagine dei volantini compare la parola, e il prezzo lo leggi tu aprendo la
  pagina. Le sto leggendo a mano, un reparto per volta: compariranno senza che tu debba fare
  niente.</p>
  <p>Se ti serve <b>qualcosa che nel catalogo non c'è</b>, scrivilo nella casella in fondo al
  cassetto: puoi mettere anche più nomi separati da virgola — per esempio
  <i>tovaglioli, salviette</i> — e la pagina cerca le pagine dove compare almeno uno di quelli.</p>
  <p>Le righe segnate <span class="ev">da controllare</span> vengono da riassunti trovati
  online e possono essere sbagliate: di errori così ne ho già trovati tre.</p>
  <p>Certi prezzi valgono <b>solo con la tessera</b> — soci Coop, Lidl Plus, Bennet Club — e
  qualche riga confronta cose diverse fra loro: il caffè in capsule al chilo costa sempre molto
  più del macinato, e l'ammorbidente non è detersivo. Sta scritto nella riga.</p>
  <p>Le parole le ha lette il computer dalle immagini: sulle scritte grandi spesso sbaglia. Se
  un prodotto dà zero pagine può esserci lo stesso, prova a chiamarlo in un altro modo.</p>

  </div>

  <h2>Quando arrivano le offerte nuove <button type="button" class="info" aria-expanded="false" aria-label="Mostra la spiegazione">i</button></h2>
  <div class="dettaglio" hidden>
  <p>I prezzi qui sopra sono dei volantini <b id="letto"></b>. Quando escono quelli nuovi
  <b>la pagina si aggiorna da sola</b>: chi l'ha aperta col link ricarica e vede i prezzi nuovi,
  senza premere niente e senza che nessuno debba rimandare niente. Vale per chiunque abbia il
  link, da qualsiasi telefono.</p>
  <p>L'unica copia che <b>non</b> si aggiorna è il file salvato sul telefono: quello resta fermo
  al giorno in cui è stato fatto. Se ti interessa avere sempre i prezzi giusti, usa il link.</p>
  <p id="p-lista"></p>
  <p>Un prodotto acceso adesso mostra <b>subito le pagine</b> dove compare, ma i
  <b>prezzi arrivano dopo</b>: quelli vanno letti dalle pagine dei volantini a occhio, non c'è
  modo di ricavarli da soli. Quando li ho letti compaiono anche quelli, senza che dobbiate
  rifare niente.</p>

  </div>

  <h2>I volantini</h2>
  <ul class="vol" id="vol"></ul>
  <p style="margin-top:12px">Su ogni riga ci sono due tasti, e tutti e due aprono
  <b>una pagina nuova</b>, così non perdi quello che stavi guardando:
  <b>«Le offerte»</b> ti mostra i prezzi letti da quel volantino, reparto per reparto;
  <b>«Il volantino»</b> apre le sue pagine sul sito di chi lo pubblica.</p>
  <p style="margin-top:12px">Di Mercatò si legge il volantino del punto vendita di
  <b>via Filadelfia 232</b>. Mercatò Local, Big ed Extra sono insegne diverse con volantini
  diversi: quello di via Demargherita, per dire, è un Local e queste offerte non sono le sue.</p>
</section>

<footer id="pie"></footer>
</div>

<!-- LA FINESTRA DELL'AIUTO. Chiesta da Manlio il 2026-09-21: «un pulsantino
     con scritto sopra aiuto, di fianco a quello di novità». Il testo l'ha letto
     e approvato prima che la facessi — l'unico pezzo che ha tolto era un
     «due cose da sapere» sui prezzi letti a mano.

     Sta fuori dal guscio e fuori dalla barra, come quella delle novità, e usa
     lo stesso vestito: una finestra sopra la pagina, non un pezzo che le
     cresce dentro. Questa pero NON si apre da sola e si puo riaprire quante
     volte si vuole: e li per quando serve. -->
<div class="buio" id="buio-aiuto" hidden>
  <div class="finestra" role="dialog" aria-modal="true" aria-labelledby="titolo-aiuto">
    <h2 id="titolo-aiuto">Come si usa</h2>
    <div class="voce">
      <h3>A cosa serve</h3>
      <p>Cerca i prodotti della tua lista nei volantini dei supermercati vicino a casa
      e ti dice dove costano meno. Il confronto è <b>per unità</b> — al chilo, al litro,
      all'uovo, al rotolo — non a confezione: è l'unico modo per capire chi costa
      davvero meno.</p>
    </div>
    <div class="voce">
      <h3>I bottoni in cima sono i tuoi prodotti</h3>
      <p>Toccane uno: sotto escono tutte le offerte, <b>dalla meno cara in giù</b>.
      Il bollino verde <b>«il meno caro»</b> sta sull'offerta che puoi comprare
      <b>oggi</b>: se la prima riga è di un volantino che deve ancora cominciare, il
      verde va a quella dopo.</p>
    </div>
    <div class="voce">
      <h3>Per cambiare i prodotti: «+ altri prodotti»</h3>
      <p>Si apre un cassetto col catalogo diviso per reparto, come il negozio. Tocca
      per accendere, tocca di nuovo per spegnere, poi «Fatto». In fondo al cassetto
      puoi anche scrivere un nome che nel catalogo non c'è.</p>
    </div>
    <div class="voce">
      <h3>Il tasto rosso «Cerca fra i prezzi»</h3>
      <p>Serve a trovare <b>una singola offerta</b> fra tutte quelle lette: scrivi una
      marca, un formato o il nome di un negozio. È un'altra cosa dalla casella dentro
      il cassetto, che invece accende i prodotti della lista.</p>
    </div>
    <div class="voce">
      <h3>Cosa dice ogni riga</h3>
      <p>Il numero grande a sinistra è il prezzo <b>per unità</b>. Accanto: prodotto,
      negozio, formato, quanto costa la confezione e <b>fino a quando vale
      l'offerta</b>. Sotto, quando serve, una nota con le condizioni: tessera del
      negozio, surgelato, «prendi 2 paghi 1», peso sgocciolato. <b>Le offerte scadute
      spariscono da sole</b>, secondo la data del telefono.</p>
    </div>
    <div class="voce">
      <h3>«Apri la pagina … del volantino»</h3>
      <p>Apre il volantino vero del negozio, alla pagina dove sta quell'offerta.</p>
    </div>
    <div class="voce">
      <h3>In fondo: l'elenco dei volantini</h3>
      <p>Ogni riga ha due tasti: <b>«Le offerte»</b> mostra i prezzi letti da quel
      volantino, <b>«Il volantino»</b> apre le sue pagine. Si aprono in una pagina
      nuova, così non perdi il posto.</p>
    </div>
    <div class="voce">
      <h3>Il tasto «Novità»</h3>
      <p>Dice cosa è cambiato: quali volantini sono stati aggiornati, quali stanno per
      arrivare e quali prezzi si sono mossi.</p>
    </div>
    <div class="pie-finestra">
      <button type="button" class="chiudi" id="chiudi-aiuto">Ho capito</button>
    </div>
  </div>
</div>

<!-- LA FINESTRA DELLE NOVITÀ. Chiesta da Manlio il 2026-09-18: si apre da sola
     la prima volta che uno apre la pagina, e dice cosa si puo fare adesso che
     prima non si poteva. Sta FUORI dal guscio e fuori dalla barra: e una
     finestra sopra la pagina, non un pezzo che le cresce dentro. -->
<div class="buio" id="buio" hidden>
  <div class="finestra" role="dialog" aria-modal="true" aria-labelledby="titolo-novita">
    <h2 id="titolo-novita">Cosa c'è di nuovo</h2>
    <p class="sotto-titolo">Non i prezzi — quelli stanno nel tasto «Novità» in alto.
    Qui c'è cosa si può fare adesso che prima non si poteva.</p>
    <div id="voci-novita"></div>
    <div class="pie-finestra">
      <button type="button" class="chiudi" id="chiudi-novita">Ho capito</button>
    </div>
  </div>
</div>

<script>
const DATI = __DATI__;

/* La lista non e piu solo mia: vive DENTRO questa pagina pubblicata, cosi la
   vedono e la cambiano tutti quelli che hanno il link. Quando qualcuno la
   tocca, la pagina si ripubblica con la lista nuova dentro e ogni schermo
   aperto si ricarica su quella. Vedi NOTE.md per il perche di questa strada
   invece della memoria sul server. */
const LISTA_PUBBLICATA = __LISTA__;
const TEMPLATE = __TEMPLATE__;

/* Vero solo nella copia pubblicata su Claude, dove la lista e davvero
   condivisa e comanda quella dentro la pagina. Sul sito e falso: li dentro non
   c'e niente che possa aggiornare la lista incorporata, quindi comanda quella
   che l'utente si e fatto nel suo browser, altrimenti le sue modifiche
   sparirebbero a ogni ricaricamento. */
const CONDIVISA = __CONDIVISA__;
const CHIAVE = 'spesa.lista.v1';
const CHIAVE_VISTI = 'spesa.visti.v1';

/* Rimette insieme il documento intero con dentro una lista nuova. L'ordine
   conta: prima la lista, poi il template. Al contrario, il template appena
   infilato porterebbe dentro un altro __LISTA__ e verrebbe riempito quello
   sbagliato. Le barre si spezzano in <\/ perche il tag di chiusura dello
   script, scritto per esteso dentro una stringa, chiuderebbe lo script per
   davvero: il browser lo cerca nel testo, non gli importa che sia in una
   stringa o in un commento. */
function documento(nuova) {
  const l = JSON.stringify(nuova).split('</').join('<\\/');
  const t = JSON.stringify(TEMPLATE).split('</').join('<\\/');
  /* Il modello va SEMPRE per ultimo: appena infilato porta dentro una copia di
     tutti gli altri segnaposto, e da quel momento replace() troverebbe quelli
     invece dei veri. Chi si ripubblica e sempre la copia condivisa. */
  return TEMPLATE
    .replace('__LISTA__', () => l)
    .replace('__CONDIVISA__', () => 'true')
    .replace('__TEMPLATE__', () => t);
}

const norm = s => (s || '').toLowerCase()
  .normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/['\u2019]/g, ' ');
/* i detersivi stanno sotto i 20 centesimi a lavaggio: con due decimali
   diventerebbero tutti «0,14 €» e non si distinguerebbero piu */
const eur = n => (n < 1 ? n.toFixed(3) : n.toFixed(2)).replace('.', ',');

/* Iniziale maiuscola sul nome che si legge, chiesto da Manlio: scriveva
   «biscotti» e se lo ritrovava minuscolo in mezzo agli altri. Si tocca solo la
   prima lettera, non ogni parola: «Olio d'oliva» deve restare cosi, e
   text-transform:capitalize del CSS lo storpierebbe in «Olio D'oliva».
   Le parole con cui si cerca restano minuscole: tanto il confronto le
   abbassa comunque. */
const maiuscola = t => (t || '').charAt(0).toUpperCase() + (t || '').slice(1);

/* Dove la lista e condivisa comanda quella dentro la pagina: e quella che
   vedono tutti, e viene aggiornata ripubblicando. Dove non lo e (il sito, il
   file) comanda quella che l'utente si e fatto: nessuno aggiornera mai quella
   incorporata, che li vale solo come punto di partenza. */
function leggiLista() {
  const dentro = Array.isArray(LISTA_PUBBLICATA) && LISTA_PUBBLICATA.length
    ? LISTA_PUBBLICATA.map(riaggancia) : null;
  if (CONDIVISA && dentro) return dentro;
  try {
    const g = localStorage.getItem(CHIAVE);
    if (g) { const v = JSON.parse(g); if (Array.isArray(v) && v.length) return aggiungiNuovi(v.map(riaggancia), dentro); }
  } catch (e) { /* memoria non disponibile: si riparte da quella incorporata */ }
  /* «dentro» è la lista incorporata quando la pagina è stata generata, e non è
     mai vuota. Il ramo di scorta lascia la lista vuota invece di ripescare una
     seconda copia: fino al 2026-09-05 la lista di partenza viaggiava DUE volte
     nella pagina, una come LISTA_PUBBLICATA e una dentro DATI. Con il catalogo,
     una lista vuota non è più un vicolo cieco: si apre «+ altri prodotti». */
  return dentro || [];
}

/* I PRODOTTI NUOVI ARRIVANO ANCHE SUL TELEFONO DI CHI HA GIA UNA SUA LISTA.
   Sul sito la lista vive nel browser di chi apre, e appena uno la tocca quella
   salvata comanda per sempre. Risultato visto il 2026-09-05: Manlio aveva
   aggiunto «Dentifricio» giorni prima, e i quattro prodotti chiesti da lui il
   4 settembre — biscotti, yogurt, marmellata, cioccolato — sul suo telefono
   non sono mai comparsi. Ha aperto la pagina, ha cercato lo yogurt di cui gli
   avevo appena parlato, e non c'era.

   Quindi: un prodotto della lista pubblicata che questo telefono non ha MAI
   visto viene aggiunto. Uno che ha visto e poi tolto NON torna: i nomi visti
   si segnano a parte e restano segnati anche dopo che il prodotto e stato
   tolto. Senza quella memoria, ogni cancellazione sarebbe stata annullata al
   ricaricamento dopo — che e il baco opposto, e peggiore. */
function visti() {
  try {
    const g = localStorage.getItem(CHIAVE_VISTI);
    const v = g ? JSON.parse(g) : null;
    return Array.isArray(v) ? v : null;
  } catch (e) { return null; }
}
function segnaVisti(nomi) {
  try {
    const dentro = visti() || [];
    nomi.forEach(n => { if (!dentro.some(x => norm(x) === norm(n))) dentro.push(n); });
    localStorage.setItem(CHIAVE_VISTI, JSON.stringify(dentro));
  } catch (e) { /* pazienza: al massimo un prodotto tolto ricompare una volta */ }
}
function aggiungiNuovi(mia, pubblicata) {
  if (!pubblicata) return mia;
  const gia = visti();
  /* La prima volta la memoria dei visti non c'e ancora: allora contano per
     visti i prodotti che questo telefono ha in lista adesso, e i mancanti
     sono davvero prodotti nuovi mai arrivati fin qui. */
  const noti = gia || mia.map(v => v.nome);
  const nuovi = pubblicata.filter(x => !noti.some(n => norm(n) === norm(x.nome))
                                    && !mia.some(v => norm(v.nome) === norm(x.nome)));
  segnaVisti(pubblicata.map(x => x.nome).concat(mia.map(v => v.nome)));
  if (!nuovi.length) return mia;
  arrivati = nuovi.map(x => maiuscola(x.nome));
  const unita = mia.concat(nuovi.map(x => ({ ...x })));
  /* Salvare subito, non aspettare che tocchi qualcosa: al caricamento dopo i
     nuovi risultano gia visti e non verrebbero riaggiunti, cioe sparirebbero
     un'altra volta. */
  try { localStorage.setItem(CHIAVE, JSON.stringify(unita)); } catch (e) {}
  return unita;
}

/* Una lista salvata da una versione vecchia della pagina puo avere prodotti
   senza categoria — quando i prezzi letti a mano coprivano solo carne, tonno e
   salmone. Qui si riattaccano ai prezzi che nel frattempo sono arrivati, senza
   toccare i nomi che l'utente si e scelto. Chi ha aggiunto un prodotto suo che
   non corrisponde a niente resta com'e. */
function riaggancia(v) {
  if (!v || !v.nome) return v;
  v = { ...v, nome: maiuscola(v.nome) };
  /* Una categoria salvata prima puo non esistere piu. Il 2026-09-05 «Detersivo»
     si e diviso in lavatrice, lavastoviglie e ammorbidente: chi aveva quel
     bottone si sarebbe ritrovato un prodotto che non trova piu nessun prezzo,
     senza capire perche. Quindi una categoria che il catalogo non conosce si
     butta e si riprova ad agganciare dal nome. */
  if (v.cat && !DATI.catalogo.some(x => x.nome === v.cat)) v = { ...v, cat: null };
  if (v.cat) return v;
  const nomi = [v.nome].concat(v.parole || []).map(norm);
  const seme = DATI.catalogo.find(x =>
    nomi.includes(norm(x.nome)) || (x.parole || []).some(w => nomi.includes(norm(w))));
  if (!seme) return v;
  const parole = (v.parole || []).slice();
  seme.parole.forEach(p => { if (!parole.some(x => norm(x) === norm(p))) parole.push(p); });
  return { nome: maiuscola(v.nome), parole, cat: seme.nome };
}
function salvaLocale() {
  segnaVisti(lista.map(v => v.nome));   // cosi un prodotto tolto non ricompare
  try { localStorage.setItem(CHIAVE, JSON.stringify(lista)); }
  catch (e) { /* la pagina funziona lo stesso, solo non ricorda */ }
}

let arrivati = [];       // prodotti nuovi comparsi in questo caricamento
let ART = null;          // la capacita di ripubblicare, se questa vista ce l'ha
let soloMio = true;      // finche non sappiamo il contrario, la lista e solo qui
let attesa = null;       // per non ripubblicare a ogni singolo tocco

function stato(testo, brutto) {
  const e = document.getElementById('stato-lista');
  if (!e) return;
  e.textContent = testo;
  e.className = 'stato' + (brutto ? ' brutto' : '');
}

/* Si ripubblica dopo un attimo, non a ogni tocco: chi ne toglie tre di fila
   fa una pubblicazione sola invece di tre, e gli altri schermi si ricaricano
   una volta sola. */
function salva() {
  salvaLocale();
  if (!ART || soloMio || !TEMPLATE) return;
  stato('Sto salvando per tutti…');
  clearTimeout(attesa);
  attesa = setTimeout(async () => {
    try {
      await ART.publish(documento(lista));
      stato('Salvata. La vedono tutti quelli che hanno il link.');
    } catch (err) {
      const c = err && err.code;
      if (c === 'conflict') {
        /* qualcun altro ha salvato nel frattempo: ogni schermo si ricarica
           sulla sua versione, quindi qui non si insiste */
        stato('Nel frattempo l\'ha cambiata qualcun altro: fra un attimo vedi la sua.');
      } else if (c === 'not_writer' || c === 'not_granted') {
        soloMio = true;
        stato('Puoi solo guardare la lista di chi te l\'ha mandata: le tue modifiche restano su questo telefono.', true);
      } else {
        stato('Non sono riuscito a salvarla per tutti. Resta su questo telefono.', true);
      }
    }
  }, 1200);
}


let lista = leggiLista();
let scelto = 0;
let tutteLePagine = false;

/* Le offerte gia in corso prima, quelle che devono ancora cominciare dopo.
   I volantini nuovi si leggono in anticipo — quello dell'Eurospin letto il
   5 settembre partiva il 10 — e senza questo si sarebbero piazzate in cima
   con tanto di bollo «il meno caro» pur non valendo ancora niente in cassa. */
/* «2026-09-10» -> «dal 10 settembre»: la data grezza in mezzo a un bollo non
   si legge, e l'anno non serve a chi guarda le offerte di questa settimana.
   L'8 e l'11 vogliono «dall'», non «dal»: il bollo diceva «vale dal 8
   settembre» e si leggeva come una svista. */
const MESI = ('gennaio febbraio marzo aprile maggio giugno luglio agosto '
  + 'settembre ottobre novembre dicembre').split(' ');
function soloGiorno(iso) {
  if (!iso) return '';
  const p = iso.split('-');
  return Number(p[2]) + ' ' + MESI[Number(p[1]) - 1];
}
function giorno(iso) {
  if (!iso) return '';
  const n = Number(iso.split('-')[2]);
  return (n === 8 || n === 11 ? "dall'" : 'dal ') + soloGiorno(iso);
}

/* Scaduto e «non ancora cominciato» si decidono QUI, a ogni apertura, contro
   la data del telefono di chi guarda — non a tavolino quando la pagina viene
   fatta. Cosi una pagina lasciata li una settimana non spaccia per buone le
   offerte finite nel frattempo: al massimo non ne ha di nuove. */
const OGGI_ISO = new Date().toLocaleDateString('sv');   // «2026-09-05»
const futuro  = x => !!x.inizio && x.inizio > OGGI_ISO;
const scaduto = x => !!x.fino   && x.fino   < OGGI_ISO;

/* «2026-09-09» -> «9 settembre». Le date su ogni riga servono perche i
   volantini durano periodi diversi: senza, guardando un prezzo non si sa se
   vale ancora domani o per altre due settimane. Chiesto da Manlio. */
function durata(o) {
  if (futuro(o))  return 'vale ' + giorno(o.inizio) + (o.fino ? ' al ' + soloGiorno(o.fino) : '');
  if (o.fino)     return 'fino al ' + soloGiorno(o.fino);
  return '';
}

/* UN'OFFERTA CHE DURA MENO DEL SUO VOLANTINO SI VEDE SOLO NEI GIORNI IN CUI
   VALE. Nel volantino MD dell'8-20 settembre c'e una pagina valida solo dal 18
   al 21: mostrarla prima vorrebbe dire mandare Manlio in negozio a chiedere un
   prezzo che non gli fanno. Un VOLANTINO INTERO non ancora cominciato invece
   resta visibile con «vale dal»: quello e voluto, serve a sapere cosa arriva.
   La differenza e che li e tutto il volantino, e si vede. */
const nascosta = o => scaduto(o) || (o.ristretta && futuro(o));

/* IN ORDINE DI PREZZO E BASTA, dal 2026-09-05.
   Prima le offerte dei volantini non ancora cominciati venivano spinte in
   fondo, qualunque prezzo avessero. Manlio se n'e accorto: «quando si
   aggiungono nuove cose vanno in fondo anche se hanno un prezzo piu basso,
   dovrebbero proprio essere in ordine di prezzo». Ha ragione: un elenco
   ordinato per prezzo che poi non lo e in fondo non e un elenco ordinato, e
   il prezzo piu basso finiva dove nessuno lo guarda.
   Il «da quando vale» non si perde: resta il bollo rosso sulla riga. Quello
   che si sposta e solo dove sta scritta. */
const offerteDi = v => v.cat
  ? DATI.offerte.filter(o => o.cat === v.cat && !nascosta(o))
  : [];

/* «Il meno caro» e il meno caro CHE SI PUO COMPRARE OGGI, non la prima riga.
   Con l'ordine per prezzo la prima riga puo essere di un volantino che parte
   fra una settimana: dargli il bollo verde vorrebbe dire mandare Manlio in
   negozio a chiedere un prezzo che non gli fanno ancora — e lasciare senza
   bollo l'offerta che invece stasera gli farebbero. */
const menoCaroOggi = off => off.find(o => !futuro(o));

/* Le pagine dei volantini dove compare almeno uno dei nomi del prodotto.
   Se non ha nomi alternativi si cerca il nome stesso. */
/* PAROLE INTERE, NON PEZZI DI PAROLA.
   Prima si guardava se il termine comparisse dentro il testo della pagina, in
   qualunque posizione: «oro» (di Oro Saiwa) lo trovava dentro «loro», «cola»
   dentro «piccola», «anca» dentro «bianca». Manlio se n'è accorto da fuori:
   «per pizza surgelata appaiono pagine nelle quali la pizza non c'entra
   niente». Quarantacinque pagine su sessantanove erano rumore, per i biscotti.

   E si tiene conto di QUANTE parole ha preso ogni pagina: una che ne ha tre
   parla davvero di quel prodotto, una che ne ha una può essere una ricetta che
   nomina la pizza di sfuggita. Le migliori vanno in cima, e ogni riga dice
   quali parole ha trovato, così si giudica invece di indovinare. */
const pagineDi = v => {
  const termini = (v.parole && v.parole.length ? v.parole : [v.nome]).map(norm);
  return DATI.pagine
    .map(p => {
      const dentro = new Set(norm(p.parole).split(' '));
      const prese = termini.filter(t => dentro.has(t));
      return prese.length ? { ...p, prese } : null;
    })
    .filter(Boolean)
    .sort((a, b) => b.prese.length - a.prese.length);
};

/* tutti i nomi di un prodotto: quello sul bottone piu gli altri con cui cercarlo */
function nomiDi(v) {
  const out = [v.nome];
  (v.parole || []).forEach(p => { if (norm(p) !== norm(v.nome)) out.push(p); });
  return out;
}

/* Un prodotto si puo chiamare in piu modi, e il volantino ne usa uno solo:
   «detersivo» o «lavatrice», «carne di bue» o «bovino». Qui si scrivono tutti,
   separati da virgola, e la pagina cerca le pagine dove compare ALMENO UNO.
   Il primo nome e quello che si legge sul bottone, gli altri lavorano sotto.
   Se uno dei nomi e gia noto (uno dei dodici di partenza, o una delle sue
   parole), si porta dietro anche i prezzi letti a mano e le sue parole. */
function costruisci(testo) {
  const termini = testo.split(/[,;]+/).map(x => x.trim()).filter(Boolean);
  if (!termini.length) return null;
  let seme = null;
  for (const t of termini) {
    const n = norm(t);
    seme = DATI.catalogo.find(x => norm(x.nome) === n || (x.parole || []).some(w => norm(w) === n));
    if (seme) break;
  }
  const parole = [];
  for (const p of termini.concat(seme ? seme.parole : [])) {
    if (!parole.some(x => norm(x) === norm(p))) parole.push(p);
  }
  return { nome: maiuscola(termini[0]), parole, cat: seme ? seme.nome : null };
}

/* ---------- barra dei prodotti ---------- */
function disegnaTasti() {
  const box = document.getElementById('tasti');
  box.textContent = '';
  lista.forEach((v, i) => {
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'tasto'; b.textContent = v.nome;
    b.setAttribute('aria-pressed', String(i === scelto));
    b.onclick = () => {
      const cambiato = scelto !== i;
      scelto = i; tutteLePagine = false;
      if (cassettoAperto) apriCassetto(false);
      disegna();
      if (cambiato) inCima();
    };
    box.appendChild(b);
  });
  const piu = document.createElement('button');
  piu.type = 'button'; piu.className = 'tasto agg';
  piu.textContent = cassettoAperto ? 'Chiudi' : '+ altri prodotti';
  piu.setAttribute('aria-expanded', String(cassettoAperto));
  piu.setAttribute('aria-controls', 'cassetto');
  piu.onclick = () => { apriCassetto(!cassettoAperto); };
  box.appendChild(piu);

  /* «Cerca fra i prezzi» e un'altra cosa dal cassetto, e vanno tenute
     separate. Il cassetto sceglie QUALI PRODOTTI stanno nella lista, e cerca
     fra le 67 voci del catalogo. Questa cerca fra le OFFERTE vere, tutte,
     anche di prodotti che in lista non ci sono e magari non ci vanno: uno
     vuole sapere quanto costa quella marca li, una volta sola, senza
     accendersi un bottone per sempre. Chiesto da Manlio il 2026-09-15,
     quando i prezzi erano diventati milleduecento. */
  const cer = document.createElement('button');
  /* Tiene anche «agg»: e la classe con cui tutte le prove riconoscono i
     bottoni che NON sono prodotti della lista. Toglierla lo farebbe contare
     come un prodotto in mezzo agli altri. Il rosso arriva da «.tasto.trova»,
     scritto dopo «.tasto.agg» nel foglio di stile, e vince lui. */
  cer.type = 'button'; cer.className = 'tasto agg trova';
  cer.textContent = ricercaAperta ? 'Chiudi' : 'Cerca fra i prezzi';
  cer.setAttribute('aria-expanded', String(ricercaAperta));
  cer.setAttribute('aria-controls', 'ricerca');
  cer.onclick = () => { apriRicerca(!ricercaAperta); };
  box.appendChild(cer);
}

/* IL CASSETTO. Chiesto da Manlio il 2026-09-05: scrivere il nome di un
   prodotto per aggiungerlo era scomodo, e chi non ero io non poteva farlo.
   Adesso c'e un catalogo gia pronto, diviso per reparto come il negozio, e
   ognuno accende i suoi. La fila dei bottoni in cima resta identica: chi non
   tocca «+ altri prodotti» non si accorge nemmeno che il catalogo esiste. */
let cassettoAperto = false;

function apriCassetto(si) {
  cassettoAperto = si;
  if (si && ricercaAperta) apriRicerca(false);   // uno alla volta
  const c = document.getElementById('cassetto');
  c.hidden = !si;
  /* Col cassetto aperto l'elenco dei prezzi di prima non c'entra più niente e
     stava lì sotto a confondere: Manlio l'ha visto subito. Torna quando si
     chiude, sul prodotto che nel frattempo si è acceso. */
  document.getElementById('risultato').hidden = si;
  disegnaTasti();
  /* Niente focus sulla casella: aprendo il cassetto faceva saltare su la
     tastiera del telefono, che copre mezzo schermo proprio mentre uno vuole
     guardarsi i reparti. Chi vuole cercare la tocca. */
  if (si) disegnaScaffali();
  else document.getElementById('cerca').value = '';
}

/* ---------- cercare fra tutti i prezzi ---------- */
let ricercaAperta = false;
let quantiMostrati = 40;

/* Con un volantino scelto dai tasti in fondo, lo stesso pannello mostra le
   offerte di QUEL volantino invece dei risultati di una parola. E lo stesso
   pannello apposta: e gia fuori dalla barra (se cresce dentro la barra il
   telefono si pianta a ogni scorrimento) e le sue righe non portano il
   bollino verde, che qui vorrebbe dire «il meno caro di questo negozio» e si
   leggerebbe «il meno caro di tutti». */
let filtroVol = null;
const SCRITTA_Q = document.getElementById('q').placeholder;

function apriRicerca(si, senzaFuoco) {
  ricercaAperta = si;
  if (si && cassettoAperto) apriCassetto(false);
  document.getElementById('ricerca').hidden = !si;
  /* Col pannello aperto l'elenco di prima non c'entra piu niente e sta li a
     confondere, come per il cassetto. */
  document.getElementById('risultato').hidden = si;
  disegnaTasti();
  if (si) {
    quantiMostrati = 40;
    disegnaTrovati();
    /* QUI il fuoco sulla casella CI VA, al contrario del cassetto. La regola
       del 2026-09-05 («niente focus, la tastiera copre mezzo schermo») valeva
       per chi apre il cassetto per GUARDARSI i reparti. Qui uno ha appena
       toccato «Cerca»: vuole scrivere, e fargli fare un secondo tocco sulla
       casella e solo una seccatura.
       ECCEZIONE: quando il pannello si apre da solo per mostrare un volantino
       intero non c'e niente da scrivere, e la tastiera coprirebbe le offerte
       appena arrivate. */
    if (!senzaFuoco) { try { document.getElementById('q').focus(); } catch (e) {} }
  } else {
    document.getElementById('q').value = '';
    document.getElementById('q').placeholder = SCRITTA_Q;
    filtroVol = null;
    /* Via la coda «#volantino=...» dall'indirizzo: se no chi ricarica questa
       scheda dopo aver chiuso il pannello se lo ritrova aperto. */
    if (location.hash) {
      try { history.replaceState(null, '', location.pathname + location.search); } catch (e) {}
    }
  }
}

/* Apre il pannello sulle offerte di un volantino solo. Lo chiamano i tasti in
   fondo (di solito in una scheda nuova) e l'indirizzo con «#volantino=». */
function apriVolantino(pdf) {
  filtroVol = pdf;
  const q = document.getElementById('q');
  q.value = '';
  q.placeholder = 'Cerca dentro questo volantino…';
  apriRicerca(true, true);
}

/* Tutte le parole scritte devono comparire da qualche parte nella riga: cosi
   «tonno rio» trova i Rio Mare e «mozzarella bennet» solo quelle del Bennet.
   Qui si cerca dentro le parole, non a parola intera come nell'indice delle
   pagine: li il testo veniva dall'OCR ed era pieno di rumore, qui sono nomi di
   prodotto scritti a mano, e chi scrive «mozzar» si aspetta di trovarli. */
function cercaOfferte(testo) {
  const parole = norm(testo).split(/\s+/).filter(x => x.length > 1);
  if (!parole.length && !filtroVol) return [];
  return DATI.offerte
    .filter(o => !nascosta(o))
    .filter(o => !filtroVol || o.pdf === filtroVol)
    .filter(o => {
      const pagliaio = norm([o.pro, o.ins, o.cat, o.fmt, o.note].join(' '));
      return parole.every(w => pagliaio.indexOf(w) >= 0);
    })
    .sort((a, b) => a.unitario - b.unitario);
}

function disegnaTrovati() {
  const testo = document.getElementById('q').value;
  const box = document.getElementById('trovati');
  const capo = document.getElementById('quanti-trovati');
  box.textContent = '';
  const parole = norm(testo).split(/\s+/).filter(x => x.length > 1);
  if (!parole.length && !filtroVol) {
    capo.innerHTML = 'Scrivi almeno due lettere. Cerca fra <b>tutte</b> le offerte '
      + 'dei volantini: il nome del prodotto, la marca, il negozio, il formato.';
    return;
  }
  const trovate = cercaOfferte(testo);
  if (!trovate.length) {
    /* Senza parola scritta e senza offerte il volantino e finito: dirlo com'e,
       invece di far credere che sia colpa di come uno ha cercato. */
    capo.innerHTML = filtroVol
      ? (parole.length
         ? '<b>Niente.</b> In questo volantino non c\u2019e nessuna offerta con questa '
           + 'parola. Cancellala e tornano tutte.'
         : '<b>Questo volantino e finito.</b> Le sue offerte non valgono piu: '
           + 'guarda quelle dei volantini in corso.')
      : '<b>Niente.</b> Prova con una parola sola, o piu corta: '
        + 'i nomi sono quelli stampati sul volantino, non sempre quelli che diresti tu.';
    return;
  }
  /* Niente bollino verde qui dentro. «Il meno caro» vuol dire il meno caro
     della sua categoria, e in un elenco di risultati direbbe una cosa falsa:
     cercando «tonno rio mare» il primo sarebbe il Rio Mare meno caro, non il
     tonno meno caro. Una novita falsa manda uno in negozio. Per il confronto
     vero c'e il bottone del prodotto. */
  capo.innerHTML = '';
  if (filtroVol) {
    /* Col volantino scelto il titolo deve dire QUALE, se no uno non sa cosa
       sta guardando: di Lidl ce ne sono due validi insieme, e di Bennet pure. */
    const v = DATI.volantini.find(x => x.pdf === filtroVol);
    const b = document.createElement('b');
    b.textContent = v ? v.ins + ' — ' + v.periodo : 'questo volantino';
    capo.appendChild(b);
    capo.appendChild(document.createTextNode(': ' + trovate.length
      + (trovate.length === 1 ? ' offerta' : ' offerte')
      + (parole.length ? ' con questa parola' : '')
      + ', divise per reparto e dalla meno cara in giù dentro ognuno. Sono solo quelle '
      + 'di questo volantino: per sapere qual è il meno caro fra tutti i negozi tocca '
      + 'il bottone del prodotto.'));
  } else {
    capo.textContent = trovate.length === 1
      ? 'Una sola offerta. Dal meno caro in giu, ma solo fra quelle che hai cercato: '
        + 'per sapere qual e il meno caro in assoluto tocca il bottone del prodotto.'
      : trovate.length + ' offerte, dalla meno cara in giu — ma solo fra quelle che hai '
        + 'cercato: per il meno caro in assoluto tocca il bottone del prodotto.';
  }

  /* Raggruppate per categoria, e le categorie in ordine di prezzo migliore:
     cercando «barilla» esce prima la pasta e poi i sughi, non alla rinfusa. */
  const gruppi = [];
  trovate.slice(0, quantiMostrati).forEach(o => {
    const c = o.cat || '—';
    let g = gruppi.find(x => x.cat === c);
    if (!g) { g = { cat: c, righe: [] }; gruppi.push(g); }
    g.righe.push(o);
  });
  gruppi.forEach(g => {
    const f = document.createElement('p');
    f.className = 'fascia';
    f.textContent = g.cat;
    box.appendChild(f);
    g.righe.forEach(o => box.appendChild(rigaPrezzo(o, false)));
  });
  if (trovate.length > quantiMostrati) {
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'altre';
    b.textContent = 'Mostra le altre ' + (trovate.length - quantiMostrati) + ' offerte';
    b.onclick = () => { quantiMostrati = trovate.length; disegnaTrovati(); };
    box.appendChild(b);
  }
}

function inLista(nome) {
  return lista.some(v => norm(v.nome) === norm(nome) || norm(v.cat || '') === norm(nome));
}

function accendi(nome) {
  const voce = DATI.catalogo.find(x => x.nome === nome);
  if (!voce) return;
  if (inLista(nome)) {
    /* Spegnendo si toglie sia il prodotto col suo nome sia quello che punta a
       quella categoria con un nome diverso: se no il bottone resta li. */
    lista = lista.filter(v => norm(v.nome) !== norm(nome) && norm(v.cat || '') !== norm(nome));
    if (scelto >= lista.length) scelto = Math.max(0, lista.length - 1);
  } else {
    lista.push({ nome: voce.nome, parole: voce.parole.slice(), cat: voce.nome });
    scelto = lista.length - 1;
    tutteLePagine = false;
  }
  salva(); disegnaScaffali(); disegna();
}

function disegnaScaffali() {
  const box = document.getElementById('scaffali');
  const cerca = document.getElementById('cerca');
  const filtro = norm(cerca ? cerca.value.trim() : '');
  box.textContent = '';
  /* Tutto in un mucchietto a parte, e dentro la pagina in un colpo solo: prima
     si infilavano i nove reparti uno per uno, e il telefono rifaceva i conti
     nove volte con la roba che cresceva sotto. Si vedeva: comparivano le prime
     categorie, poi si piantava. */
  const mucchio = document.createDocumentFragment();
  let quanti = 0;
  DATI.reparti.forEach(rep => {
    const voci = DATI.catalogo.filter(v => v.rep === rep && (!filtro
      || norm(v.nome).includes(filtro) || v.parole.some(w => norm(w).includes(filtro))));
    if (!voci.length) return;
    quanti += voci.length;
    const h = document.createElement('p');
    h.className = 'reparto'; h.textContent = rep;
    mucchio.appendChild(h);
    const fila = document.createElement('div');
    fila.className = 'tasti';
    voci.forEach(v => {
      const b = document.createElement('button');
      b.type = 'button'; b.className = 'tasto'; b.textContent = v.nome;
      b.setAttribute('aria-pressed', String(inLista(v.nome)));
      b.onclick = () => accendi(v.nome);
      fila.appendChild(b);
    });
    mucchio.appendChild(fila);
  });
  box.appendChild(mucchio);
  const f = document.getElementById('fuori-catalogo');
  f.textContent = quanti
    ? 'Non c\u2019\u00e8 quello che cerchi? Scrivilo qui sopra: cerco la parola nelle pagine dei volantini.'
    : 'Nel catalogo non c\u2019\u00e8 niente con questo nome. Scrivilo lo stesso qui sopra: cerco la parola nelle pagine dei volantini.';
}

/* Cambiando prodotto si torna all'inizio del suo elenco.
   Manlio: scorreva i prezzi del tonno, toccava «Suino», e si ritrovava in
   mezzo alla lista del suino invece che in cima — perche la pagina cambiava
   sotto ma la finestra restava dov'era. Non si torna in cima alla pagina: si
   va al primo prezzo, appena sotto la barra dei bottoni, che resta attaccata
   in alto. Cosi si vede subito quale bottone e acceso e da dove parte
   l'elenco. Se si e gia lassu non si muove niente. */
function inCima() {
  const r = document.getElementById('risultato');
  const barra = document.querySelector('.barra');
  if (!r) return;
  const alto = barra ? barra.getBoundingClientRect().height : 0;
  /* Il taglio a zero va fatto PRIMA del confronto, non dopo: con una meta
     negativa «sono gia sopra?» risponde sempre no, e la pagina chiederebbe di
     scorrere anche stando gia in cima. */
  const meta = Math.max(0, r.getBoundingClientRect().top + (window.scrollY || 0) - alto - 8);
  if ((window.scrollY || 0) <= meta) return;      // gia sopra: fermo dov'e
  try { window.scrollTo({ top: meta, behavior: 'smooth' }); }
  catch (e) { window.scrollTo(0, meta); }
}

/* ---------- righe ---------- */
/* «meno» non vuol dire «prima riga»: e il meno caro fra quelli che valgono
   oggi. Le righe sono in ordine di prezzo, e la prima puo essere di un
   volantino che deve ancora cominciare. */
function rigaPrezzo(o, meno) {
  const d = document.createElement('article');
  d.className = 'prezzo-riga';
  d.innerHTML = `<div><p class="nome"></p><p class="sotto"></p></div>
    <p class="val"><span class="n"></span><span class="u"></span></p>
    <div class="coda"></div>`;
  d.querySelector('.nome').textContent = o.pro;
  const s = d.querySelector('.sotto');
  s.innerHTML = '<b></b> · <span></span> · <span></span>';
  s.querySelector('b').textContent = o.ins;
  s.querySelectorAll('span')[0].textContent = o.fmt;
  s.querySelectorAll('span')[1].textContent = eur(o.prezzo) + ' € la confezione';
  const q = durata(o);
  if (q) {
    const d2 = document.createElement('span');
    d2.className = 'quando' + (o.ristretta ? ' stretta' : '');
    d2.textContent = q;
    s.appendChild(document.createTextNode(' · '));
    s.appendChild(d2);
  }
  d.querySelector('.val .n').textContent = eur(o.unitario) + ' €';
  d.querySelector('.val .u').textContent = DATI.unita[o.cat] || 'al kg';
  const coda = d.querySelector('.coda');
  if (meno) coda.insertAdjacentHTML('beforeend', '<span class="bollo meno">il meno caro</span>');
  if (o.ristretta) coda.insertAdjacentHTML('beforeend',
    '<span class="bollo stretta">solo ' + giorno(o.inizio) + ' al ' + soloGiorno(o.fino) + '</span>');
  else if (futuro(o)) coda.insertAdjacentHTML('beforeend',
    '<span class="bollo dopo">vale ' + giorno(o.inizio) + '</span>');
  if (o.dubbio) coda.insertAdjacentHTML('beforeend', '<span class="bollo dubbio">da controllare</span>');
  if (!coda.children.length) coda.remove();
  if (o.note) {
    const n = document.createElement('p'); n.className = 'nota'; n.textContent = o.note;
    d.appendChild(n);
  }
  d.appendChild(dove(o));
  return d;
}

/* La riga che dice dov'e l'offerta. Se so l'indirizzo della pagina diventa un
   collegamento che apre il volantino a quella pagina: prima c'era scritto
   «pagina 16» e Manlio doveva arrangiarsi. Si apre in una scheda nuova, cosi
   non perde la lista. */
function dove(o) {
  if (!o.url) {
    const p = document.createElement('p');
    p.className = 'dove';
    p.textContent = o.pag ? `${o.pdf} — pagina ${o.pag}` : `${o.pdf} — pagina non individuata`;
    return p;
  }
  const a = document.createElement('a');
  a.className = 'dove apri';
  a.href = o.url;
  a.target = '_blank';
  a.rel = 'noopener noreferrer';
  a.textContent = `Apri la pagina ${o.pag} del volantino`;
  return a;
}

function rigaPagina(p) {
  const d = document.createElement(p.url ? 'a' : 'div');
  d.className = 'pag-riga' + (p.url ? ' apribile' : '');
  if (p.url) { d.href = p.url; d.target = '_blank'; d.rel = 'noopener noreferrer'; }
  d.innerHTML = `<span><span class="ins"></span><span class="per"></span></span><span class="np"></span>`;
  d.querySelector('.ins').textContent = p.ins;
  d.querySelector('.per').textContent = (p.prese && p.prese.length)
    ? 'ci ho trovato: ' + p.prese.join(', ')
    : p.periodo;
  d.querySelector('.np').textContent = 'pag. ' + p.pag;
  return d;
}

/* ---------- pagina ---------- */
function disegna() {
  disegnaTasti();
  const out = document.getElementById('risultato');
  out.textContent = '';
  if (!lista.length) {
    out.innerHTML = '<p class="vuoto">La lista è vuota. Tocca «+ aggiungi» per rimetterci qualcosa.</p>';
    return;
  }
  if (scelto >= lista.length) scelto = lista.length - 1;

  const v = lista[scelto];
  const off = offerteDi(v), pag = pagineDi(v);

  /* SOTTO IL NOME DEL PRODOTTO NON CI VA PIÙ NIENTE.
     Manlio, 2026-09-05, foto alla mano: «toglierei tutto quello che c'è
     scritto dopo carne di bue e lascerei solo una piccola scritta o un'icona
     per cancellarla». Quanti prezzi ci sono, con che altri nomi si cerca e il
     cambio nome sono roba da guardare una volta ogni tanto: stanno dietro il
     bollino «i», come le spiegazioni in fondo. Restano il nome e la crocetta. */
  const capo = document.createElement('div');
  capo.className = 'capo';
  /* Il bottone dice cosa fa. Prima c'era una crocetta, e Manlio: «la x per
     togliere il prodotto mi sembra poco comprensibile, metterei invece un
     bottone elimina prodotto». La «i» viene subito dopo, come ha chiesto. */
  capo.innerHTML = '<h2></h2>'
    + '<button type="button" class="elimina">Elimina prodotto</button>'
    + '<button type="button" class="info" aria-expanded="false"'
    + ' aria-label="Mostra i dettagli del prodotto">i</button>';
  capo.querySelector('h2').textContent = v.nome;
  capo.querySelector('.elimina').setAttribute('aria-label', 'Elimina «' + v.nome + '» dalla lista');
  out.appendChild(capo);

  /* La crocetta è piccola e sta accanto al nome: un tocco per sbaglio non deve
     far sparire un prodotto. Chiede conferma lì dove si è toccato, senza
     finestrelle di sistema che sul telefono arrivano da tutt'altra parte. */
  const conferma = document.createElement('div');
  conferma.className = 'conferma';
  conferma.hidden = true;
  conferma.innerHTML = '<span></span><button type="button" class="si">Elimina</button>'
    + '<button type="button" class="no">Lascia</button>';
  conferma.querySelector('span').textContent = 'Elimino «' + v.nome + '»?';
  conferma.querySelector('.si').onclick = () => {
    lista.splice(scelto, 1);
    if (scelto > 0) scelto--;
    salva(); disegna();
  };
  conferma.querySelector('.no').onclick = () => { conferma.hidden = true; };
  capo.querySelector('.elimina').onclick = () => { conferma.hidden = !conferma.hidden; };
  out.appendChild(conferma);

  const dett = document.createElement('div');
  dett.className = 'dettaglio';
  dett.hidden = true;

  const quanti = document.createElement('p');
  quanti.className = 'quanti';
  quanti.textContent = off.length
    ? `${off.length} ${off.length === 1 ? 'offerta letta' : 'offerte lette'} dal volantino · ${pag.length} pagine da guardare`
    : `${pag.length} ${pag.length === 1 ? 'pagina lo nomina' : 'pagine lo nominano'}`;
  dett.appendChild(quanti);

  const altri = nomiDi(v).slice(1);
  if (altri.length) {
    const p = document.createElement('p');
    p.className = 'sinonimi';
    p.innerHTML = '<span></span> ';
    p.querySelector('span').textContent = 'cerca anche:';
    altri.forEach(a => {
      const c = document.createElement('em');
      c.textContent = a;
      p.appendChild(c);
    });
    dett.appendChild(p);
  }

  const g = document.createElement('div');
  g.className = 'gestisci';
  const bRin = document.createElement('button');
  bRin.type = 'button'; bRin.textContent = 'Cambia nome';
  g.appendChild(bRin);
  dett.appendChild(g);

  const fr = document.createElement('form');
  fr.className = 'form-rin';
  fr.innerHTML = '<input type="text" aria-label="Nomi del prodotto, separati da virgola"><button type="submit">Salva</button>';
  const inp = fr.querySelector('input');
  fr.onsubmit = ev => {
    ev.preventDefault();
    const t = inp.value.trim();
    if (!t) return;
    const v2 = costruisci(t);
    if (!v2) return;
    lista[scelto] = v2;
    salva(); disegna();
  };
  bRin.onclick = () => {
    fr.classList.add('on');
    inp.value = nomiDi(v).join(', ');
    inp.focus(); inp.select();
  };
  dett.appendChild(fr);
  out.appendChild(dett);

  capo.querySelector('.info').onclick = () => {
    const apri = dett.hidden;
    dett.hidden = !apri;
    capo.querySelector('.info').setAttribute('aria-expanded', String(apri));
  };

  if (off.length) {
    const f = document.createElement('p');
    f.className = 'fascia'; f.textContent = 'Prezzi letti dal volantino';
    out.appendChild(f);
    const meno = menoCaroOggi(off);
    off.forEach(o => out.appendChild(rigaPrezzo(o, o === meno)));
  } else if (v.cat && DATI.offerte.some(o => o.cat === v.cat)) {
    /* I prezzi c'erano e sono tutti scaduti. Dirlo, invece di far comparire il
       vuoto: senza questa riga sembrerebbe che il prodotto non sia mai stato
       in offerta da nessuna parte. */
    const p = document.createElement('p');
    p.className = 'vuoto';
    p.textContent = 'I volantini che avevano questo prodotto sono tutti scaduti, '
      + 'e quelli nuovi non li ho ancora letti. Qui sotto ci sono comunque le pagine.';
    out.appendChild(p);
  }

  const f2 = document.createElement('p');
  f2.className = 'fascia';
  f2.textContent = off.length ? 'Altre pagine che lo nominano' : 'Pagine da guardare';
  out.appendChild(f2);

  if (pag.length) {
    const quante = tutteLePagine ? pag.length : 10;
    pag.slice(0, quante).forEach(p => out.appendChild(rigaPagina(p)));
    if (pag.length > quante) {
      const b = document.createElement('button');
      b.type = 'button'; b.className = 'altre';
      b.textContent = `Mostra le altre ${pag.length - quante} pagine`;
      b.onclick = () => { tutteLePagine = true; disegna(); };
      out.appendChild(b);
    }
  } else {
    const p = document.createElement('p');
    p.className = 'vuoto';
    p.textContent = 'Il computer non ha letto questa parola in nessuna pagina. Può esserci lo stesso: prova a chiamare il prodotto in un altro modo, con una parola più comune.';
    out.appendChild(p);
  }
}

/* ---------- volantini in fondo ---------- */
const ul = document.getElementById('vol');
DATI.volantini.forEach(v => {
  const li = document.createElement('li');
  li.innerHTML = `<div class="capo-vol"><span><span class="i"></span> <span class="p"></span></span><span class="n"></span></div>`;
  li.querySelector('.i').textContent = v.ins;
  li.querySelector('.p').textContent = v.periodo
    + (scaduto(v) ? ' — scaduto' : futuro(v) ? ' — non ancora cominciato' : '');
  if (scaduto(v) || futuro(v)) li.querySelector('.p').style.color = 'var(--ambra)';
  li.querySelector('.n').textContent = v.pagine + ' pag.';

  /* I DUE TASTI, chiesti da Manlio il 2026-09-18: «visto che alla fine c'e
     l'elenco dei supermercati, un tasto per vedere le offerte e uno per vedere
     il volantino». Tutti e due aprono una scheda nuova, come ha chiesto: chi
     guarda non perde la lista ne il punto in cui era. */
  const tasti = document.createElement('div');
  tasti.className = 'vol-tasti';

  /* Quante ne valgono OGGI, non quante ne ho lette: di un volantino scaduto
     non c'e niente da aprire, e il tasto lo direbbe per finta. Il conto lo fa
     il browser di chi guarda, con la sua data, come tutto il resto. */
  const quante = DATI.offerte.filter(o => o.pdf === v.pdf && !nascosta(o)).length;
  if (quante) {
    const a = document.createElement('a');
    a.className = 'vol-t';
    a.href = location.href.split('#')[0] + '#volantino=' + encodeURIComponent(v.pdf);
    a.target = '_blank';
    a.rel = 'noopener';
    a.textContent = 'Le offerte (' + quante + ')';
    /* La scheda nuova si apre a mano, e non per capriccio: dentro la copia di
       Claude la pagina sta in una cornice che a volte la scheda nuova non la
       lascia aprire. Se non si apre, invece di non fare niente si apre il
       pannello qui, sulla stessa pagina: meglio un tasto che funziona in un
       modo un po' diverso di un tasto che non fa niente. */
    a.onclick = ev => {
      ev.preventDefault();
      let nuova = null;
      try { nuova = window.open(a.href, '_blank'); } catch (e) { nuova = null; }
      if (nuova) { try { nuova.opener = null; } catch (e) {} return; }
      apriVolantino(v.pdf);
      inCima();
    };
    tasti.appendChild(a);
  } else {
    const spento = document.createElement('span');
    spento.className = 'vol-t spento';
    spento.textContent = scaduto(v) ? 'offerte scadute'
      : futuro(v) ? 'prezzi in arrivo' : 'prezzi non ancora letti';
    tasti.appendChild(spento);
  }

  if (v.apri) {
    const b = document.createElement('a');
    b.className = 'vol-t fuori';
    b.href = v.apri;
    b.target = '_blank';
    b.rel = 'noopener noreferrer';
    b.textContent = 'Il volantino';
    tasti.appendChild(b);
  }
  li.appendChild(tasti);
  ul.appendChild(li);
});

/* Ogni bollino «i» apre e chiude il pannello che gli sta subito dopo il
   titolo. Un solo giro per tutti: aggiungendo una sezione basta scriverci il
   bollino e il pannello, senza toccare questo. */
document.querySelectorAll('.info').forEach(b => {
  /* h1 O h2: il primo bollino di questa pagina stava in un h2, e cercare solo
     quello bastava. Aggiungendone uno nel titolone in cima, closest('h2') ha
     dato niente e la pagina è uscita MUTA — bottoni compresi, perché l'errore
     fermava tutto il resto dello script. È lo stesso guasto del tag di
     chiusura scritto per esteso: da fuori sembra a posto e non funziona
     niente. Se un giorno un bollino finisce in un h3, va aggiunto qui. */
  const testa = b.closest('h1, h2');
  const pannello = testa && testa.nextElementSibling;
  if (!pannello || !pannello.classList.contains('dettaglio')) return;
  b.onclick = () => {
    const apri = pannello.hidden;
    pannello.hidden = !apri;
    b.setAttribute('aria-expanded', String(apri));
    b.setAttribute('aria-label', apri ? 'Nascondi la spiegazione' : 'Mostra la spiegazione');
  };
});

document.getElementById('cerca').oninput = disegnaScaffali;
document.getElementById('chiudi-cassetto').onclick = () => apriCassetto(false);
document.getElementById('chiudi-ricerca').onclick = () => apriRicerca(false);
document.getElementById('q').addEventListener('input', () => {
  quantiMostrati = 40;
  disegnaTrovati();
});

document.getElementById('form-agg').onsubmit = ev => {
  ev.preventDefault();
  const c = document.getElementById('nuovo');
  const t = c.value.trim();
  if (!t) return;
  const v2 = costruisci(t);
  if (!v2) return;
  lista.push(v2);
  scelto = lista.length - 1;
  tutteLePagine = false;
  c.value = '';
  apriCassetto(false);
  salva(); disegna();
};


/* Una data sola per tutta la pagina. Prima quella in fondo era scritta a mano e
   restava indietro: la pagina diceva 4 settembre in mezzo e 2 settembre in fondo,
   e se n'e accorto Manlio. */
document.getElementById('letto').textContent = 'letti il ' + DATI.letto;
document.getElementById('pie').textContent =
  'Volantini letti il ' + DATI.letto + '. I numeri di pagina sono quelli dei volantini.';
aggiornaTestoLista();

/* Cosa dire della lista dipende dalla copia che si sta guardando: sul sito e
   una per telefono, sulla copia di Claude e una sola per tutti. Scriverne una
   sola delle due era una bugia per meta dei lettori. */
function aggiornaTestoLista() {
  const p = document.getElementById('p-lista');
  if (!p) return;
  p.innerHTML = soloMio
    ? '<b>La lista dei prodotti è tua e resta su questo telefono.</b> Puoi aggiungere e '
      + 'togliere quello che vuoi senza toccare quella di nessun altro. Chi apre da un altro '
      + 'telefono riparte dai prodotti di partenza e se la regola per conto suo.'
    : '<b>La lista dei prodotti è una sola, condivisa.</b> Chi apre il link vede la stessa, e se '
      + 'la cambia la cambia per tutti. Quando qualcuno la tocca, gli altri schermi si aggiornano '
      + 'da soli.';
}


disegna();

/* «#volantino=...» in coda all'indirizzo: e quello che i tasti in fondo mettono
   nella scheda nuova. Qui si legge e si apre subito il pannello con le offerte
   di quel volantino. Se non corrisponde a niente non succede niente: meglio la
   pagina normale che un pannello vuoto. */
(function daIndirizzo() {
  const m = /^#volantino=(.+)$/.exec(location.hash || '');
  if (!m) return;
  let pdf = '';
  try { pdf = decodeURIComponent(m[1]); } catch (e) { return; }
  if (!DATI.volantini.some(v => v.pdf === pdf)) return;
  apriVolantino(pdf);
  /* Nella scheda nuova si arriva in cima, con lo schermo pieno di bottoni, e
     le offerte appena aperte restano mezze sotto. Un piccolo scorrimento le
     porta subito sotto la barra: chi ha toccato «Le offerte» vuole vedere
     quelle, non la fila dei prodotti. */
  try {
    const pan = document.getElementById('ricerca');
    const barra = document.querySelector('.barra');
    const alto = barra ? barra.getBoundingClientRect().height : 0;
    window.scrollTo(0, Math.max(0, pan.getBoundingClientRect().top + (window.scrollY || 0) - alto - 8));
  } catch (e) {}
})();

/* ---------- la finestra delle novità DELLA PAGINA ---------- */
/* Chiesta da Manlio il 2026-09-18. Si apre da sola la prima volta, e dice cosa
   si puo fare adesso che prima non si poteva: l'interfaccia, non i prezzi. I
   prezzi nuovi hanno gia il tasto «Novità» in alto a destra.

   Chi ha gia visto tutto non la rivede piu: nel browser di chi guarda resta
   l'id dell'ultima novita vista, e la volta dopo compaiono SOLO quelle
   arrivate dopo. Gli id cominciano con la data apposta: e cosi che «dopo»
   diventa un confronto fra due scritte, senza tenere elenchi.

   Se il browser non lascia leggere ne scrivere (navigazione privata, memoria
   piena), la finestra si comporta come per uno nuovo: si apre. Meglio una
   volta di troppo che una pagina che non funziona. */
const NOVITA_VISTE = 'spesa.novita.v1';

function novitaDaMostrare() {
  const tutte = DATI.novita || [];
  if (!tutte.length) return [];
  let vista = '';
  try { vista = localStorage.getItem(NOVITA_VISTE) || ''; } catch (e) { vista = ''; }
  if (!vista) return tutte;
  return tutte.filter(n => n.id > vista);
}

function mostraNovita() {
  const buio = document.getElementById('buio');
  if (!buio) return;
  const da = novitaDaMostrare();
  if (!da.length) { buio.hidden = true; return; }
  const box = document.getElementById('voci-novita');
  box.textContent = '';
  da.forEach(n => {
    const d = document.createElement('div');
    d.className = 'voce';
    d.innerHTML = '<span class="quando"></span><h3></h3><p></p>';
    d.querySelector('.quando').textContent = n.quando;
    d.querySelector('h3').textContent = n.titolo;
    d.querySelector('p').textContent = n.testo;
    box.appendChild(d);
  });
  buio.hidden = false;
  /* Il fuoco sul tasto SENZA muovere la pagina: con lo scorrimento in automatico
     la finestra si apriva gia scorsa in fondo e il titolo non si vedeva. */
  try { document.getElementById('chiudi-novita').focus({ preventScroll: true }); } catch (e) {}
  try { document.querySelector('.finestra').scrollTop = 0; } catch (e) {}
}

/* Chiudendo si segna l'ULTIMA della lista, non l'ultima mostrata: se uno apre
   per la prima volta le vede tutte, e da li in poi conta solo quello che
   arriva dopo. */
function chiudiNovita() {
  const buio = document.getElementById('buio');
  if (!buio || buio.hidden) return;
  buio.hidden = true;
  const tutte = DATI.novita || [];
  if (tutte.length) {
    try { localStorage.setItem(NOVITA_VISTE, tutte[tutte.length - 1].id); } catch (e) {}
  }
}

/* ---------- la finestra dell'aiuto ---------- */
/* Al contrario di quella delle novita non si apre mai da sola e non si ricorda
   niente: si apre quando uno tocca «Aiuto» e si chiude in tre modi, il tasto,
   il buio intorno, il tasto Esc. */
function apriAiuto(si) {
  const buio = document.getElementById('buio-aiuto');
  if (!buio) return;
  if (si) chiudiNovita();            // una finestra alla volta
  buio.hidden = !si;
  if (si) {
    try { document.getElementById('chiudi-aiuto').focus({ preventScroll: true }); } catch (e) {}
    try { buio.querySelector('.finestra').scrollTop = 0; } catch (e) {}
  }
}

document.getElementById('apri-aiuto').onclick = () => apriAiuto(true);
document.getElementById('chiudi-aiuto').onclick = () => apriAiuto(false);
document.getElementById('buio-aiuto').onclick = ev => {
  if (ev.target.id === 'buio-aiuto') apriAiuto(false);
};

document.getElementById('chiudi-novita').onclick = chiudiNovita;
/* Il buio intorno chiude, la finestra no: toccando dentro non deve sparire. */
document.getElementById('buio').onclick = ev => { if (ev.target.id === 'buio') chiudiNovita(); };
addEventListener('keydown', ev => {
  if (ev.key !== 'Escape') return;
  chiudiNovita();
  apriAiuto(false);
});
mostraNovita();

/* Va in fondo, DOPO che «lista» e stata creata e la pagina disegnata una prima
   volta. Messo prima, chiamava disegna() quando «lista» non esisteva ancora e
   moriva li: i bottoni comparivano lo stesso (li disegnava la chiamata in
   fondo) ma sotto non usciva niente. La capacita, dove c'e, arriva comunque
   dopo il primo giro di questo script: la pagina deve funzionare gia prima e
   accendersi quando arriva. */
(async () => {
  try {
    ART = window.claude && claude.use ? await claude.use('artifact') : null;
  } catch (e) { ART = null; }
  if (ART) {
    soloMio = false;
    lista = leggiLista();
  } else {
    /* La riga sotto i bottoni dice SOLO le novità di adesso. «Questa copia è
       solo tua» è vero per sempre e stava lì a occupare due righe di schermo:
       Manlio l'ha evidenziata fra le cose da togliere. È finita dietro il
       bollino in cima, dove si va a leggere quando si vuole. */
    stato(arrivati.length ? 'Aggiunti alla tua lista: ' + arrivati.join(', ') + '.' : '');
  }
  const dv = document.getElementById('dove-vive');
  if (dv) dv.textContent = soloMio
    ? 'Questa copia è solo tua: quello che cambi resta su questo telefono.'
    : 'Questa copia è condivisa: quello che cambi lo vede anche chi ha il link.';
  aggiornaTestoLista();
  disegna();
})();
</script>'''

# ---------------------------------------------------------------------------
# Il documento contiene una copia di se stesso, cosi puo ripubblicarsi con una
# lista nuova dentro senza perdere la capacita di rifarlo la volta dopo.
#
#   CORPO    = la pagina come la vuole il servizio (senza <html>/<head>: li
#              mette lui), con dentro i due segnaposto
#   COMPLETO = lo stesso, ma documento intero: e questo che la pagina
#              ripubblica di sua iniziativa, e quindi e questo che si porta
#              dietro come modello
#
# I segnaposto restano NON risolti dentro COMPLETO: e proprio quello che
# permette alla generazione dopo di riempirli di nuovo. Prima la lista e poi il
# modello, altrimenti il modello appena infilato porta dentro un altro
# __LISTA__ e si riempie quello sbagliato.
# ---------------------------------------------------------------------------
def racchiudi(testo):
    """JSON da mettere dentro un <script>: </script> va spezzato o chiude il tag."""
    return json.dumps(testo, ensure_ascii=False).replace('</', '<\\/')

CORPO = HTML.replace('__DATI__', DATI)

INTESTA = ('<!doctype html>\n<html lang="it">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
           '<style>body{margin:0}img{max-width:100%}</style>\n')
COMPLETO = (INTESTA + CORPO + '\n</body>\n</html>\n').replace(
    '</style>\n\n<div class="guscio">', '</style>\n</head>\n<body>\n<div class="guscio">', 1)

def riempi(modello):
    """Riempie SOLO la prima occorrenza di ogni segnaposto.

    I due segnaposto compaiono due volte ciascuno: una e quella vera, in cima
    allo script, l'altra e la stringa dentro documento() che serve a
    sostituirla la volta dopo. Riempiendole tutte e due si rompe documento() e
    il file cresce di 200 KB inutili. La prima e sempre quella vera, perche le
    due costanti sono dichiarate sopra la funzione; in JavaScript replace() con
    una stringa si ferma alla prima da solo, quindi le due parti si comportano
    allo stesso modo."""
    # il modello per ultimo: vedi documento() nello script, stessa trappola
    return (modello
            .replace('__LISTA__', LISTA0, 1)
            .replace('__CONDIVISA__', 'true', 1)
            .replace('__TEMPLATE__', racchiudi(COMPLETO), 1))

open('out/pagina.html', 'w', encoding='utf-8').write(riempi(CORPO))

# Copia che si apre a doppio clic, senza account e senza rete. Non puo
# ripubblicare (non c'e nessun window.claude), quindi niente modello e niente
# lista condivisa: li la lista e di chi apre e resta nel suo browser.
open('out/spesa-da-sola.html', 'w', encoding='utf-8').write(
    COMPLETO.replace('__LISTA__', LISTA0, 1)
            .replace('__TEMPLATE__', '""', 1)
            .replace('__CONDIVISA__', 'false', 1))

# ---------------------------------------------------------------------------
# La versione per il sito vero (GitHub Pages). Li dentro non esiste
# window.claude, quindi la pagina non potra mai ripubblicarsi: il modello e
# peso morto e lo si toglie (230 KB in meno). Ha invece il manifest e il suo
# service worker, per potersi installare sul telefono e funzionare in negozio
# senza segnale.
# ---------------------------------------------------------------------------
TESTA_SITO = ('<link rel="manifest" href="./manifest.webmanifest">\n'
              '<meta name="theme-color" content="#FFFFFF">\n'
              '<meta name="apple-mobile-web-app-title" content="Spesa">\n')
CODA_SITO = '''<script>
/* Un service worker suo, in questa cartella. Serve a due cose: tenere la
   pagina disponibile senza rete (in negozio il segnale e pessimo) e togliere
   di mezzo quello della Palestra, che ha lo scope sopra e senza rete
   servirebbe l'app della palestra al posto di questa. */
if ('serviceWorker' in navigator) {
  addEventListener('load', () => navigator.serviceWorker.register('./sw.js').catch(() => {}));
}
</script>
'''
sito = (COMPLETO
        .replace('<meta name="viewport" content="width=device-width, initial-scale=1">\n',
                 '<meta name="viewport" content="width=device-width, initial-scale=1">\n' + TESTA_SITO, 1)
        .replace('\n</body>\n</html>\n', '\n' + CODA_SITO + '</body>\n</html>\n', 1)
        .replace('__LISTA__', LISTA0, 1)
        .replace('__TEMPLATE__', '""', 1)
        .replace('__CONDIVISA__', 'false', 1))
open('out/sito.html', 'w', encoding='utf-8').write(sito)
print('sito:', len(sito) // 1024, 'KB (senza la copia di se stessa)')


# ---------------------------------------------------------------------------
# CONTROLLO OBBLIGATORIO, non un lusso.
#
# Il 2026-09-03 un commento conteneva il tag di chiusura dello script scritto
# per esteso. Il browser lo cerca nel testo e non gli importa che sia dentro un
# commento: ha chiuso lo script a meta e tutte e tre le pagine sono uscite
# morte, quella gia in mano a Manlio compresa. Da fuori sembravano a posto —
# intestazione, riquadri, tutto — solo senza prodotti.
#
# Qui si spezza ogni file dove il browser lo spezzerebbe e si controlla che
# ogni pezzo sia JavaScript valido e che quello grosso contenga davvero la
# funzione che disegna la pagina. Se non torna, il file NON si consegna.
# ---------------------------------------------------------------------------
def controlla(percorso):
    import re, subprocess, tempfile
    testo = open(percorso, encoding='utf-8').read()
    pezzi = re.findall(r'<script>(.*?)</script>', testo, re.S)
    if not pezzi:
        raise SystemExit(f'{percorso}: nessuno script trovato')
    for n, pezzo in enumerate(pezzi):
        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as t:
            t.write(pezzo); tmp = t.name
        esito = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
        os.unlink(tmp)
        if esito.returncode != 0:
            riga = esito.stderr.strip().split(chr(10))
            raise SystemExit(f'{percorso}: il pezzo {n} non e JavaScript valido\n  '
                             + chr(10).join('  ' + r for r in riga[:4]))
    if 'function disegna' not in pezzi[0]:
        raise SystemExit(f'{percorso}: lo script principale e stato tagliato prima di '
                         'disegna(). Quasi certamente c\'e un tag di chiusura scritto '
                         'per esteso in un commento o in una stringa.')
    print(f'  {os.path.basename(percorso):24s} {len(pezzi)} script, tutti validi')

print('controllo che le pagine non siano spezzate:')
for f in ('out/pagina.html', 'out/sito.html', 'out/spesa-da-sola.html'):
    controlla(f)

print('scritta —', len(riempi(CORPO)) // 1024, 'KB;', len(partenza), 'prodotti in lista,',
      len(offerte), 'prezzi,', len(pagine), 'pagine indicizzate')
