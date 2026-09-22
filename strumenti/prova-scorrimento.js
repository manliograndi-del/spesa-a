/* Cambiando prodotto la pagina deve riportare in cima all'elenco nuovo.

   Manlio, 2026-09-05: «quando si schiaccia un altro bottone appare l'altra
   lista del nuovo prodotto ma non dall'inizio, all'altezza alla quale si era
   lasciata la lista precedente».

   jsdom non impagina: se lo si lascia fare, ogni misura viene zero e la prova
   passa senza aver controllato il conto. Quindi qui le misure gliele diamo noi
   — elenco che comincia a 420 dall'alto della pagina, barra dei bottoni alta
   150 — e si pretende che la pagina risalga esattamente a 262, cioe al primo
   prezzo appena sotto la barra. */
const fs = require('fs');
const { JSDOM, VirtualConsole } = require('jsdom');
const dom = new JSDOM(fs.readFileSync(process.argv[2], 'utf8'), {
  runScripts: 'dangerously', pretendToBeVisual: true,
  url: 'https://manliograndi-del.github.io/spesa-a/',
  virtualConsole: new VirtualConsole(),
});
setTimeout(() => {
  const w = dom.window, d = w.document;
  const chiamate = [];
  w.scrollTo = (a) => chiamate.push(typeof a === 'object' ? a.top : a);
  const tasti = [...d.querySelectorAll('.tasto')].filter(b => !b.classList.contains('agg'));
  const guai = [];

  const CIMA_ELENCO = 420, ALTA_BARRA = 150, ATTESA = CIMA_ELENCO - ALTA_BARRA - 8;
  d.getElementById('risultato').getBoundingClientRect =
    () => ({ top: CIMA_ELENCO - (w.scrollY || 0), height: 3000 });
  d.querySelector('.barra').getBoundingClientRect = () => ({ top: 0, height: ALTA_BARRA });

  // finge di aver scorso in giu, e cambia DAVVERO prodotto
  // (tasti[0] e gia quello acceso: toccarlo di nuovo non e un cambio)
  Object.defineProperty(w, 'scrollY', { value: 4000, configurable: true });
  chiamate.length = 0;
  tasti[2].click();
  if (!chiamate.length) guai.push('cambiando prodotto dopo aver scorso, non risale');
  else if (chiamate[0] !== ATTESA)
    guai.push(`risale a ${chiamate[0]} invece che a ${ATTESA} (il primo prezzo sotto la barra)`);
  console.log(`  scorso in basso, cambio prodotto → risale a ${chiamate[0] ?? 'niente'} (atteso ${ATTESA})`);

  // ritoccando lo stesso bottone non deve muoversi
  chiamate.length = 0;
  tasti[2].click();
  if (chiamate.length) guai.push('ritoccando lo stesso bottone si muove');
  console.log('  stesso bottone di nuovo → ' + (chiamate.length ? 'si muove (male)' : 'fermo'));

  // gia in cima (o comunque sopra il primo prezzo): non deve muoversi
  Object.defineProperty(w, 'scrollY', { value: 0, configurable: true });
  chiamate.length = 0;
  tasti[1].click();
  if (chiamate.length) guai.push('già in cima e si muove lo stesso');
  console.log('  già in cima, cambio prodotto → ' + (chiamate.length ? 'si muove (male)' : 'fermo'));

  if (guai.length) { console.log('\nNON VA:'); guai.forEach(g => console.log('  ✗ ' + g)); process.exit(1); }
  console.log('  lo scorrimento si comporta bene');
  process.exit(0);
}, 2500);
