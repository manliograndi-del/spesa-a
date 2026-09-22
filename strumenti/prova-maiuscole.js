/* Simula il telefono di Manlio: lista salvata nel browser coi nomi minuscoli,
   come li aveva scritti lui. La pagina deve mostrarli con l'iniziale grande
   senza che lui tocchi niente. */
const fs = require('fs');
const { JSDOM, VirtualConsole } = require('jsdom');
// Il file si passa da fuori, come fanno tutte le altre prove. Qui c'era
// incollato il percorso della cartella di lavoro di una sessione vecchia:
// quella cartella e sparita con la sessione, e da allora questa prova
// falliva sempre — cioe l'ultimo passo di prove.sh non provava piu niente.
const file = process.argv[2] || 'out/sito.html';

const sua = JSON.stringify([
  { nome: 'Carne di bue', parole: ['bovino','scottona'], cat: 'Carne di bue' },
  { nome: "olio d'oliva", parole: ['olio','oliva'], cat: "Olio d'oliva" },
  { nome: 'biscotti', parole: ['biscotti'], cat: null },
  { nome: 'yogurt', parole: ['yogurt'], cat: null },
  { nome: 'marmellata', parole: ['marmellata'], cat: null },
  { nome: 'cioccolato', parole: ['cioccolato'], cat: null },
]);

const errori = [];
const dom = new JSDOM(fs.readFileSync(file, 'utf8'), {
  runScripts: 'outside-only', url: 'https://manliograndi-del.github.io/spesa-a/',
});
dom.window.localStorage.setItem('spesa.lista.v1', sua);
const dom2 = new JSDOM(fs.readFileSync(file, 'utf8'), {
  runScripts: 'dangerously', pretendToBeVisual: true,
  url: 'https://manliograndi-del.github.io/spesa-a/',
  virtualConsole: new VirtualConsole().on('jsdomError', e => errori.push(String(e.detail || e.message).split('\n')[0])),
  beforeParse(w) { w.localStorage.setItem('spesa.lista.v1', sua); },
});

setTimeout(() => {
  const d = dom2.window.document;
  const nomi = [...d.querySelectorAll('#tasti .tasto')].filter(b => !b.classList.contains('agg')).map(b => b.textContent);
  console.log('nomi sui bottoni:', nomi.join(' · '));
  const minuscoli = nomi.filter(n => n[0] !== n[0].toUpperCase());
  console.log(minuscoli.length ? 'ANCORA MINUSCOLI: ' + minuscoli.join(', ') : 'tutti con l\'iniziale maiuscola');
  console.log('«Olio d\'oliva» non storpiato:', nomi.includes("Olio d'oliva"));
  // i prezzi si riagganciano lo stesso?
  const b = [...d.querySelectorAll('#tasti .tasto')].find(x => x.textContent === 'Biscotti');
  if (b) { b.dispatchEvent(new dom2.window.MouseEvent('click', { bubbles: true }));
    console.log('cliccando «Biscotti»:', d.querySelectorAll('.prezzo-riga').length, 'prezzi'); }
  console.log(errori.length ? 'errori: ' + errori.join(' ;; ') : 'nessun errore');
  process.exit(0);
}, 2500);
