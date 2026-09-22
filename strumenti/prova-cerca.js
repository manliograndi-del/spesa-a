/* La casella che cerca fra TUTTI i prezzi, chiesta da Manlio il 2026-09-15
   quando le offerte erano diventate milleduecento e il catalogo a reparti non
   bastava piu.

   Qui si controllano le cose che, se si rompono, non si vedono rileggendo:
   - il pannello NON sta dentro la barra appiccicata (e la lezione del cassetto:
     dentro, la barra diventa piu alta dello schermo e il telefono si pianta);
   - cercare due parole restringe davvero, non allarga;
   - i risultati sono in ordine di prezzo;
   - NESSUN bollino verde «il meno caro» fra i risultati: li vorrebbe dire il
     meno caro DELLA RICERCA, non della categoria, e sarebbe una bugia che
     manda uno in negozio.                                                    */
const fs = require('fs');
const { JSDOM, VirtualConsole } = require('jsdom');
const file = process.argv[2] || 'out/sito.html';

const errori = [];
const vc = new VirtualConsole().on('jsdomError',
  e => errori.push(String(e.detail || e.message).split('\n')[0]));
const dom = new JSDOM(fs.readFileSync(file, 'utf8'), {
  runScripts: 'dangerously', pretendToBeVisual: true, virtualConsole: vc,
  url: 'https://manliograndi-del.github.io/spesa-a/',
});

setTimeout(() => {
  const w = dom.window, d = w.document;
  const male = [];
  if (errori.length) male.push('errori nella pagina: ' + errori.join(' / '));

  const tasto = [...d.querySelectorAll('#tasti .tasto')]
    .find(b => b.textContent.includes('Cerca'));
  if (!tasto) { console.error('MANCA il tasto «Cerca fra i prezzi»'); process.exit(1); }

  /* Manlio non lo vedeva: era tratteggiato e grigio come «+ altri prodotti».
     Deve restare rosso pieno e su una riga tutta sua. Se qualcuno gli rimette
     la classe «agg», questa prova se ne accorge. */
  if (!tasto.classList.contains('trova'))
    male.push('il tasto Cerca non e piu quello rosso (classe .trova)');
  const css = [...d.querySelectorAll('style')].map(s => s.textContent).join('\n');
  if (!/\.tasto\.trova\{[^}]*var\(--rosso\)/.test(css))
    male.push('il tasto Cerca non e piu rosso nel CSS');
  if (!/\.tasto\.trova\{[^}]*flex:0 0 100%/.test(css))
    male.push('il tasto Cerca non e piu su una riga tutta sua');
  tasto.dispatchEvent(new w.Event('click'));

  const pannello = d.getElementById('ricerca');
  if (!pannello || pannello.hidden) male.push('il pannello non si apre');
  if (d.querySelector('.barra').contains(pannello))
    male.push('IL PANNELLO STA DENTRO LA BARRA: si ripianta come il cassetto');
  if (!d.getElementById('risultato').hidden)
    male.push("l'elenco di prima resta li sotto a confondere");

  const cerca = q => {
    const i = d.getElementById('q');
    i.value = q;
    i.dispatchEvent(new w.Event('input'));
    return [...d.querySelectorAll('#trovati .prezzo-riga')];
  };

  const una = cerca('tonno');
  if (una.length < 3) male.push('«tonno» trova solo ' + una.length + ' offerte');
  const due = cerca('tonno rio');
  if (!(due.length && due.length < una.length))
    male.push('due parole non restringono: ' + una.length + ' -> ' + due.length);

  const prezzi = una.map(r => parseFloat(
    r.querySelector('.val .n').textContent.replace(',', '.')));
  for (let i = 1; i < prezzi.length; i++)
    if (prezzi[i] < prezzi[i - 1]) { male.push('non sono in ordine di prezzo'); break; }

  if (d.querySelectorAll('#trovati .bollo.meno').length)
    male.push('C\'E UN BOLLINO VERDE fra i risultati: direbbe una cosa falsa');

  if (cerca('a').length) male.push('una lettera sola cerca lo stesso');
  if (!d.getElementById('quanti-trovati').textContent.includes('due lettere'))
    male.push('con una lettera non spiega cosa fare');
  if (cerca('qwertyx').length) male.push('una parola inventata trova qualcosa');

  // ogni riga deve dire negozio, prezzo per unita e dove sta
  const r0 = cerca('mozzarella')[0];
  if (r0) {
    if (!r0.querySelector('.sotto b').textContent.trim()) male.push('manca il negozio');
    if (!r0.querySelector('.val .n').textContent.trim()) male.push('manca il prezzo');
    if (!r0.querySelector('.dove')) male.push('manca la riga che dice dov\'e');
  }

  // aprire il cassetto deve chiudere la ricerca, e viceversa: uno alla volta
  const piu = [...d.querySelectorAll('#tasti .tasto')]
    .find(b => b.textContent.includes('altri prodotti'));
  if (piu) {
    piu.dispatchEvent(new w.Event('click'));
    if (!d.getElementById('ricerca').hidden)
      male.push('aprendo il cassetto la ricerca resta aperta');
  }

  if (male.length) { male.forEach(x => console.error('  ✗ ' + x)); process.exit(1); }
  console.log('  «tonno»: ' + una.length + ' offerte, «tonno rio»: ' + due.length);
  console.log('  fuori dalla barra, in ordine di prezzo, nessun bollino bugiardo');
  console.log('  la casella cerca fra tutti i prezzi e funziona');
}, 1200);
