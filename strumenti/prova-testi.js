/* Controlla che la pagina non dica cose false su se stessa: la data dev'essere
   una sola, e la frase sulla lista deve dire la verita per QUESTA copia.

       node prova-testi.js out/sito.html
       node prova-testi.js out/pagina.html --condivisa

   La frase sulla lista NON dipende da come e stato generato il file: la decide
   la pagina quando parte, guardando se il servizio di Claude le risponde. In un
   browser finto non risponde mai, quindi senza --condivisa anche la copia di
   Claude direbbe «solo tua» — vero per come e stata aperta, non per com'e
   davvero. Con --condivisa si finge che risponda, ed e cosi che va provata. */
const fs = require('fs');
const { JSDOM, VirtualConsole } = require('jsdom');
const file = process.argv[2];
const condivisa = process.argv.includes('--condivisa');
const errori = [];
const dom = new JSDOM(fs.readFileSync(file, 'utf8'), {
  runScripts: 'dangerously', pretendToBeVisual: true,
  url: 'https://manliograndi-del.github.io/spesa-a/',
  beforeParse(w) {
    if (condivisa) w.claude = { use: async () => ({ publish: async () => {} }) };
  },
  virtualConsole: new VirtualConsole()
    .on('jsdomError', e => errori.push(String(e.detail || e.message).split('\n')[0])),
});
setTimeout(() => {
  const d = dom.window.document;
  const letto = d.getElementById('letto').textContent;
  const pie = d.getElementById('pie').textContent;
  const lista = d.getElementById('p-lista').textContent;
  const scaduti = [...d.querySelectorAll('#vol .p')].filter(e => /scaduto/.test(e.textContent));
  console.log('  copia provata come:', condivisa ? 'condivisa (di Claude)' : 'solo tua (sito o file)');
  console.log('  in mezzo:', letto);
  console.log('  in fondo:', pie);
  const d1 = (letto.match(/\d+ \w+ \d{4}/) || [''])[0];
  const d2 = (pie.match(/\d+ \w+ \d{4}/) || [''])[0];
  const dice_condivisa = /una sola, condivisa/.test(lista);
  const guai = [];
  if (!d1 || d1 !== d2) guai.push(`le due date non combaciano: «${d1}» e «${d2}»`);
  if (!/volantini\./.test(pie)) guai.push('il piede parla ancora di PDF');
  if (dice_condivisa !== condivisa)
    guai.push(`dice «${dice_condivisa ? 'condivisa' : 'solo tua'}» ma questa copia e l'altra cosa`);
  console.log('  le due date combaciano:', d1 === d2 && !!d1, `(${d1})`);
  console.log('  frase sulla lista:', lista.slice(0, 72) + '…');
  console.log('  volantini segnati scaduti:',
    scaduti.map(e => e.textContent.split('—')[0].trim()).join(', ') || 'nessuno');
  if (errori.length) guai.push('errori in pagina: ' + errori.join(' | '));
  if (guai.length) {
    console.log('\nNON VA:'); guai.forEach(g => console.log('  ✗ ' + g));
    process.exit(1);
  }
  console.log('  tutto vero');
  process.exit(0);
}, 2000);
