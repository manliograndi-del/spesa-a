/* Sotto il nome del prodotto non ci va niente, e in cima nemmeno.

   Manlio, 2026-09-05, foto alla mano: ha evidenziato il sottotitolo, la riga
   «questa copia è solo tua», il conteggio delle offerte, i sinonimi e il
   «Cambia nome» — «toglierei tutto quello che c'è scritto dopo carne di bue e
   lascerei solo una piccola scritta o un'icona per cancellarla».

   Questa prova pretende che a pagina appena aperta si vedano SOLO il nome, il
   bollino e la crocetta, e che il resto stia dietro il bollino. E controlla la
   crocetta: piccola com'è, non deve poter cancellare un prodotto con un tocco
   per sbaglio.                                                              */
const fs = require('fs');
const { JSDOM, VirtualConsole } = require('jsdom');
const errori = [];
const dom = new JSDOM(fs.readFileSync(process.argv[2], 'utf8'), {
  runScripts: 'dangerously', pretendToBeVisual: true,
  url: 'https://manliograndi-del.github.io/spesa-a/',
  virtualConsole: new VirtualConsole()
    .on('jsdomError', e => errori.push(String(e.detail || e.message).split('\n')[0])),
});
setTimeout(() => {
  const d = dom.window.document;
  const guai = [];
  const vede = e => !!e && !e.hidden && !e.closest('[hidden]');
  const prodotti = () => [...d.querySelectorAll('#tasti .tasto')]
    .filter(b => !b.classList.contains('agg')).length;

  if (!prodotti()) guai.push('la pagina è muta: nessun bottone in cima');

  if (vede(d.getElementById('dett-testa')))
    guai.push('il sottotitolo si vede senza toccare il bollino');
  const stato = d.getElementById('stato-lista').textContent.trim();
  if (/copia è solo tua|Lista condivisa/.test(stato))
    guai.push('la riga «questa copia è solo tua» è tornata sotto i bottoni: «' + stato + '»');

  const capo = d.querySelector('.capo');
  if (!capo) { console.log('NON VA:\n  ✗ non c’è l’intestazione del prodotto'); process.exit(1); }
  const tasti = [...capo.querySelectorAll('button')].map(b => b.className);
  console.log('  accanto al nome: ' + (tasti.join(' + ') || 'niente'));
  if (tasti.join() !== 'elimina,info')
    guai.push('accanto al nome ci sono ' + (tasti.join(' + ') || 'zero bottoni') + ', devono essere elimina + info');

  for (const [che, sel] of [['il conteggio', '#risultato .quanti'],
                            ['i sinonimi', '#risultato .sinonimi'],
                            ['«Cambia nome»', '#risultato .gestisci button']]) {
    const e = d.querySelector(sel);
    if (vede(e)) guai.push(che + ' si vede senza toccare il bollino');
  }

  capo.querySelector('.info').click();
  const q = d.querySelector('#risultato .quanti');
  if (!vede(q)) guai.push('il bollino del prodotto non apre il dettaglio');
  else console.log('  il bollino apre: ' + q.textContent);

  // la crocetta chiede conferma, e «Lascia» non cancella niente
  const prima = prodotti();
  capo.querySelector('.elimina').click();
  const conf = d.querySelector('.conferma');
  if (!vede(conf)) guai.push('«Elimina prodotto» cancella senza chiedere conferma');
  else console.log('  «Elimina prodotto» chiede: ' + conf.querySelector('span').textContent);
  conf.querySelector('.no').click();
  if (prodotti() !== prima) guai.push('«Lascia» ha cancellato lo stesso');
  d.querySelector('.capo .elimina').click();
  d.querySelector('.conferma .si').click();
  if (prodotti() !== prima - 1) guai.push('«Elimina» non ha tolto il prodotto');
  console.log(`  «Lascia» lascia (${prima}), «Elimina» elimina (${prodotti()})`);

  if (errori.length) guai.push('errori in pagina: ' + errori.join(' | '));
  if (guai.length) { console.log('\nNON VA:'); guai.forEach(g => console.log('  ✗ ' + g)); process.exit(1); }
  console.log('  in cima e sotto il nome c’è solo quello che deve esserci');
  process.exit(0);
}, 2500);
