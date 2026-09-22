/* «Le pagine da guardare» devono nominare davvero il prodotto.

   Manlio, 2026-09-05: «per pizza surgelata appaiono sotto un elenco di pagine
   del volantino nel quale la pizza non c'entra per niente». Il motivo era che
   il confronto cercava il termine DENTRO il testo, in qualunque posizione:
   «oro» (di Oro Saiwa) lo trovava dentro «loro», «cola» dentro «piccola»,
   «anca» dentro «bianca».

   Qui si pretende che ogni pagina in elenco contenga almeno una delle parole
   del prodotto COME PAROLA INTERA, che le pagine con più parole stiano in
   cima, e che ogni riga dica quali parole ci ha trovato.                   */
const fs = require('fs');
const { JSDOM, VirtualConsole } = require('jsdom');
const errori = [];
const testo = fs.readFileSync(process.argv[2], 'utf8');
/* DATI è una costante dentro lo script, non finisce su window: si legge dal
   file. Provando a prenderla da window veniva «undefined» e la prova moriva
   senza aver controllato niente. */
const DATI = JSON.parse(testo.match(/\nconst DATI = (\{.*?\});\n/s)[1]);
const dom = new JSDOM(testo, {
  runScripts: 'dangerously', pretendToBeVisual: true,
  url: 'https://manliograndi-del.github.io/spesa-a/',
  virtualConsole: new VirtualConsole()
    .on('jsdomError', e => errori.push(String(e.detail || e.message).split('\n')[0])),
});
setTimeout(() => {
  const d = dom.window.document;
  const guai = [];
  const norm = s => (s || '').toLowerCase().normalize('NFD')
    .replace(/[̀-ͯ]/g, '').replace(/['’]/g, ' ');
  const parole = new Map(DATI.pagine.map(p => [p.ins + '|' + p.pag + '|' + p.pdf,
                                               new Set(norm(p.parole).split(' '))]));
  let viste = 0, conDue = 0;

  for (const voce of DATI.catalogo) {
    const termini = voce.parole.map(norm);
    const trovate = DATI.pagine.filter(p => {
      const s = parole.get(p.ins + '|' + p.pag + '|' + p.pdf);
      return termini.some(t => s.has(t));
    });
    viste += trovate.length;
    // nessuna pagina deve entrare per un pezzo di parola
    for (const p of DATI.pagine) {
      const s = parole.get(p.ins + '|' + p.pag + '|' + p.pdf);
      const intera = termini.some(t => s.has(t));
      const pezzo = termini.some(t => norm(p.parole).includes(t));
      if (pezzo && !intera && trovate.includes(p))
        guai.push(`«${voce.nome}» prende ${p.ins} pag ${p.pag} per un pezzo di parola`);
    }
  }
  console.log(`  pagine prese in tutto dal catalogo: ${viste}`);

  // in cima quelle che ne hanno trovate di più, e la riga lo dice
  const b = [...d.querySelectorAll('#tasti .tasto')].filter(x => !x.classList.contains('agg'));
  for (const t of b) {
    t.click();
    const righe = [...d.querySelectorAll('.pag-riga .per')].map(e => e.textContent);
    const quante = righe.map(r => (r.match(/,/g) || []).length);
    for (let i = 1; i < quante.length; i++)
      if (quante[i] > quante[i - 1])
        guai.push(`«${t.textContent.trim()}»: una pagina con più parole sta sotto una con meno`);
    if (righe.length && !righe.every(r => /ci ho trovato:/.test(r)))
      guai.push(`«${t.textContent.trim()}»: una riga non dice cosa ci ha trovato`);
    if (righe.some(r => (r.match(/,/g) || []).length)) conDue++;
  }
  console.log(`  prodotti con almeno una pagina «forte»: ${conDue} su ${b.length}`);

  if (errori.length) guai.push('errori in pagina: ' + errori.join(' | '));
  if (guai.length) {
    console.log('\nNON VA:'); [...new Set(guai)].slice(0, 8).forEach(g => console.log('  ✗ ' + g));
    process.exit(1);
  }
  console.log('  le pagine in elenco nominano davvero il prodotto');
  process.exit(0);
}, 2500);
