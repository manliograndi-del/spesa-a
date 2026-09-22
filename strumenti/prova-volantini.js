/* I DUE TASTI SU OGNI VOLANTINO, chiesti da Manlio il 2026-09-18: «visto che
   alla fine c'e l'elenco dei supermercati, un tasto per vedere le offerte e
   uno per vedere il volantino», e che si aprano in pagine nuove.

   Qui si controllano le cose che, rompendosi, non si vedono rileggendo il
   codice:
   - ogni riga dell'elenco ha i suoi tasti, e quello del volantino porta al
     sito di chi lo pubblica (non a un indirizzo inventato);
   - il tasto delle offerte apre SOLO le offerte di quel volantino: se
     mostrasse anche le altre, uno andrebbe al Lidl a cercare un prezzo del
     Bennet;
   - le offerte escono dalla meno cara in giu e SENZA bollino verde: li
     dentro «il meno caro» vorrebbe dire «di questo negozio» e si leggerebbe
     «di tutti» (stessa regola della ricerca);
   - il pannello NON sta dentro la barra appiccicata (la lezione del cassetto:
     dentro, il telefono si pianta a ogni scorrimento);
   - lo stesso indirizzo aperto in una scheda nuova (con «#volantino=» in
     coda) fa la stessa cosa da solo: e cosi che i tasti aprono la pagina
     nuova.                                                                  */
const fs = require('fs');
const { JSDOM, VirtualConsole } = require('jsdom');
const file = process.argv[2] || 'out/sito.html';
const testo = fs.readFileSync(file, 'utf8');
const SITO = 'https://manliograndi-del.github.io/spesa-a/';
const male = [];

function apri(indirizzo, quando) {
  /* window.open in jsdom non esiste: la pagina se ne accorge e ripiega sul
     pannello qui, che e proprio quello che deve fare quando la scheda nuova
     non si apre. Gli «errori» di jsdom su window.open non sono errori della
     pagina, quindi si tengono da parte a parte. */
  const errori = [];
  const vc = new VirtualConsole().on('jsdomError', e => {
    const m = String(e.detail || e.message).split('\n')[0];
    if (!/window\.open|Not implemented/i.test(m)) errori.push(m);
  });
  const dom = new JSDOM(testo, {
    runScripts: 'dangerously', pretendToBeVisual: true, virtualConsole: vc, url: indirizzo,
  });
  setTimeout(() => quando(dom.window, dom.window.document, errori), 1200);
}

apri(SITO, (w, d, errori) => {
  if (errori.length) male.push('errori nella pagina: ' + errori.join(' / '));

  const righe = [...d.querySelectorAll('#vol li')];
  if (!righe.length) { console.error('MANCA l\'elenco dei volantini'); process.exit(1); }
  righe.forEach(li => {
    const t = li.querySelector('.vol-tasti');
    if (!t || !t.children.length)
      male.push('un volantino senza tasti: ' + li.textContent.trim());
  });

  /* Il tasto che apre il volantino vero: deve portare al sito di chi lo mette
     online — qui non si pubblica niente di loro — e aprirsi in sicurezza. */
  const fuori = [...d.querySelectorAll('.vol-t.fuori')];
  if (fuori.length < 2) male.push('solo ' + fuori.length + ' volantini si possono aprire');
  const brutti = fuori.filter(a =>
    !/^https:\/\/(www\.anteprimavolantino\.it|resources\.volantinopiu\.it|eu\.kimbicdn\.com|app\.ekomdiscount\.it)\//.test(a.href));
  if (brutti.length) male.push(brutti.length + ' tasti «Il volantino» portano altrove');
  if (!fuori.every(a => a.target === '_blank' && /noopener/.test(a.rel)))
    male.push('«Il volantino» non si apre in una scheda nuova, in sicurezza');

  /* Il tasto delle offerte. L'indirizzo deve essere quello della pagina stessa
     con la coda «#volantino=», se no la scheda nuova si apre su niente. */
  const offerte = [...d.querySelectorAll('.vol-t')].filter(a => /Le offerte/.test(a.textContent));
  if (!offerte.length) { console.error('MANCA il tasto «Le offerte»'); process.exit(1); }
  const noti = w.eval('DATI.volantini.map(v => v.pdf)');
  offerte.forEach(a => {
    const m = /^([^#]*)#volantino=(.+)$/.exec(a.getAttribute('href') || '');
    if (!m) { male.push('un tasto «Le offerte» senza indirizzo buono'); return; }
    if (m[1].indexOf('http') !== 0) male.push('l\'indirizzo delle offerte non e completo');
    if (noti.indexOf(decodeURIComponent(m[2])) < 0)
      male.push('un tasto «Le offerte» punta a un volantino che non esiste');
    if (a.target !== '_blank') male.push('«Le offerte» non apre una scheda nuova');
  });

  const primo = offerte[0];
  const pdf = decodeURIComponent(/#volantino=(.+)$/.exec(primo.getAttribute('href'))[1]);
  const attese = w.eval('DATI.offerte.filter(o => o.pdf === ' + JSON.stringify(pdf)
                        + ' && !nascosta(o)).length');
  if (!primo.textContent.includes('(' + attese + ')'))
    male.push('il tasto dice un numero di offerte diverso da quelle che ci sono davvero');

  primo.dispatchEvent(new w.MouseEvent('click', { bubbles: true, cancelable: true }));

  const pannello = d.getElementById('ricerca');
  if (!pannello || pannello.hidden) male.push('il pannello delle offerte non si apre');
  if (d.querySelector('.barra').contains(pannello))
    male.push('IL PANNELLO STA DENTRO LA BARRA: si ripianta come il cassetto');
  if (!d.getElementById('risultato').hidden)
    male.push('l\'elenco di prima resta li sotto a confondere');

  const mostrate = [...d.querySelectorAll('#trovati .prezzo-riga')];
  if (!mostrate.length) male.push('il pannello si apre vuoto');
  if (mostrate.length !== Math.min(attese, 40))
    male.push('mostra ' + mostrate.length + ' righe invece di ' + Math.min(attese, 40));

  const insegna = w.eval('DATI.volantini.find(v => v.pdf === ' + JSON.stringify(pdf) + ').ins');
  const estranee = mostrate.filter(r => r.querySelector('.sotto b').textContent.trim() !== insegna);
  if (estranee.length)
    male.push('fra le offerte di ' + insegna + ' ce ne sono ' + estranee.length + ' di altri negozi');

  /* In ordine di prezzo DENTRO OGNI REPARTO, come nella ricerca: il prezzo per
     unita del detersivo (a lavaggio) e quello della carne (al chilo) non si
     confrontano fra loro, e le offerte escono raggruppate per categoria. */
  let fuoriOrdine = 0, ultimo = null, dentro = null;
  [...d.querySelectorAll('#trovati > *')].forEach(el => {
    if (el.classList.contains('fascia')) { dentro = el.textContent; ultimo = null; return; }
    if (!el.classList.contains('prezzo-riga')) return;
    const v = parseFloat(el.querySelector('.val .n').textContent.replace(',', '.'));
    if (ultimo !== null && v < ultimo) fuoriOrdine++;
    ultimo = v;
  });
  if (fuoriOrdine) male.push(fuoriOrdine + ' offerte non sono in ordine di prezzo dentro il loro reparto');
  if (dentro === null) male.push('le offerte non sono divise per reparto');

  if (d.querySelectorAll('#trovati .bollo.meno').length)
    male.push('C\'E UN BOLLINO VERDE fra le offerte di un volantino solo: direbbe una cosa falsa');
  if (!d.getElementById('quanti-trovati').textContent.includes(insegna))
    male.push('il pannello non dice di quale volantino sono le offerte');

  /* Scrivendo nella casella si restringe DENTRO il volantino, non fuori. */
  const q = d.getElementById('q');
  q.value = 'pasta';
  q.dispatchEvent(new w.Event('input'));
  const strette = [...d.querySelectorAll('#trovati .prezzo-riga')];
  if (strette.length > mostrate.length)
    male.push('scrivendo una parola le offerte aumentano invece di restringersi');
  if (strette.some(r => r.querySelector('.sotto b').textContent.trim() !== insegna))
    male.push('cercando dentro il volantino escono offerte di altri negozi');

  /* «Fatto» chiude e rimette la pagina com'era: la ricerca normale torna a
     cercare fra TUTTE le offerte, non dentro l'ultimo volantino guardato. */
  d.getElementById('chiudi-ricerca').dispatchEvent(new w.Event('click'));
  if (d.getElementById('risultato').hidden) male.push('chiudendo, l\'elenco dei prodotti non torna');
  const cer = [...d.querySelectorAll('#tasti .tasto')].find(b => b.textContent.includes('Cerca'));
  cer.dispatchEvent(new w.Event('click'));
  q.value = 'mozzarella';
  q.dispatchEvent(new w.Event('input'));
  const negozi = new Set([...d.querySelectorAll('#trovati .prezzo-riga')]
    .map(r => r.querySelector('.sotto b').textContent.trim()));
  if (negozi.size < 2)
    male.push('dopo aver guardato un volantino la ricerca resta chiusa dentro quello');

  console.log('  volantini in elenco: ' + righe.length + ', apribili: ' + fuori.length);
  console.log('  «' + insegna + '»: ' + attese + ' offerte sue, mostrate ' + mostrate.length
              + ', tutte di quel volantino');

  /* La scheda nuova: stesso indirizzo con la coda, e il pannello si apre da
     solo. E quello che vede Manlio quando tocca il tasto sul telefono. */
  apri(SITO + '#volantino=' + encodeURIComponent(pdf), (w2, d2, errori2) => {
    if (errori2.length) male.push('errori aprendo la scheda nuova: ' + errori2.join(' / '));
    const p2 = d2.getElementById('ricerca');
    if (!p2 || p2.hidden) male.push('la scheda nuova non apre le offerte del volantino');
    const righe2 = [...d2.querySelectorAll('#trovati .prezzo-riga')];
    if (righe2.length !== Math.min(attese, 40))
      male.push('la scheda nuova mostra ' + righe2.length + ' righe invece di ' + Math.min(attese, 40));
    if (d2.querySelectorAll('#trovati .bollo.meno').length)
      male.push('bollino verde nella scheda nuova');

    if (male.length) { male.forEach(x => console.error('  ✗ ' + x)); process.exit(1); }
    console.log('  la scheda nuova si apre gia sulle offerte di quel volantino');
    console.log('  i due tasti dei volantini fanno quello che devono');
    process.exit(0);
  });
});
