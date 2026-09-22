/* Il cassetto: apre, mostra i reparti, cerca, accende e spegne.

   Chiesto da Manlio il 2026-09-05 al posto della casella dove si scriveva il
   nome. Le cose che devono restare vere:
     - la fila dei bottoni in cima non cambia finché non si accende qualcosa;
     - il cassetto mostra tutto il catalogo, diviso per reparto;
     - la ricerca filtra anche sulle parole del volantino, non solo sul nome
       («bovino» deve trovare «Carne di bue»);
     - accendere aggiunge il bottone, spegnere lo toglie;
     - un prodotto acceso mostra i prezzi che ha, e il bottone lo sa già.  */
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
  const inCima = () => [...d.querySelectorAll('#tasti .tasto')]
    .filter(b => !b.classList.contains('agg')).map(b => b.textContent.trim());
  const cassetto = d.getElementById('cassetto');
  const apri = d.querySelector('#tasti .tasto.agg');
  const scaffale = () => [...d.querySelectorAll('#scaffali .tasto')].map(b => b.textContent.trim());
  const reparti = () => [...d.querySelectorAll('#scaffali .reparto')].map(p => p.textContent.trim());

  const prima = inCima();
  if (!cassetto.hidden) guai.push('il cassetto è aperto senza che nessuno l’abbia toccato');

  /* Il cassetto NON deve stare dentro la barra appiccicata in alto. Ci stava,
     e aprendolo la barra diventava più alta dello schermo: il telefono di
     Manlio si piantava per qualche secondo. È il genere di guasto che non si
     vede in un browser finto, perché lì non si impagina niente — quindi qui si
     controlla la struttura, che è la causa, non la lentezza, che è l'effetto. */
  if (cassetto.closest('.barra'))
    guai.push('il cassetto sta dentro la barra appiccicata: aprendolo il telefono si blocca');

  apri.click();
  if (cassetto.hidden) guai.push('toccando «+ altri prodotti» il cassetto non si apre');
  if (inCima().join('|') !== prima.join('|')) guai.push('aprire il cassetto ha cambiato i bottoni in cima');
  console.log(`  aperto: ${scaffale().length} prodotti in ${reparti().length} reparti`);
  if (d.activeElement === d.getElementById('cerca'))
    guai.push('aprendo il cassetto la casella prende il fuoco: sul telefono salta su la tastiera');
  if (scaffale().length < 60) guai.push('nel cassetto ci sono meno di 60 prodotti');

  // i prodotti già in lista risultano accesi
  const accesi = [...d.querySelectorAll('#scaffali .tasto')]
    .filter(b => b.getAttribute('aria-pressed') === 'true').map(b => b.textContent.trim());
  console.log('  già accesi: ' + accesi.length);
  prima.forEach(n => {
    if (scaffale().includes(n) && !accesi.includes(n))
      guai.push(`«${n}» è in cima ma nel cassetto risulta spento`);
  });

  // la ricerca guarda anche le parole del volantino
  const cerca = d.getElementById('cerca');
  cerca.value = 'bovino'; cerca.dispatchEvent(new dom.window.Event('input'));
  const trovati = scaffale();
  console.log('  cercando «bovino»: ' + (trovati.join(', ') || 'niente'));
  if (!trovati.includes('Carne di bue'))
    guai.push('«bovino» non trova «Carne di bue»: la ricerca non guarda le parole del volantino');
  cerca.value = ''; cerca.dispatchEvent(new dom.window.Event('input'));

  // accendere
  const spento = [...d.querySelectorAll('#scaffali .tasto')]
    .find(b => b.getAttribute('aria-pressed') === 'false');
  const nome = spento.textContent.trim();
  spento.click();
  if (!inCima().includes(nome)) guai.push(`accendendo «${nome}» non compare in cima`);
  console.log(`  acceso «${nome}» → ${inCima().length} bottoni in cima`);

  // spegnere
  const ora = [...d.querySelectorAll('#scaffali .tasto')].find(b => b.textContent.trim() === nome);
  ora.click();
  if (inCima().includes(nome)) guai.push(`spegnendo «${nome}» resta in cima`);
  console.log(`  spento  «${nome}» → ${inCima().length} bottoni in cima`);

  // «Fatto» chiude
  d.getElementById('chiudi-cassetto').click();
  if (!cassetto.hidden) guai.push('«Fatto» non chiude il cassetto');

  // un prodotto acceso mostra i suoi prezzi
  apri.click();
  const conPrezzi = [...d.querySelectorAll('#scaffali .tasto')]
    .find(b => b.textContent.trim() === 'Mozzarella');
  if (conPrezzi) {
    if (conPrezzi.getAttribute('aria-pressed') === 'false') conPrezzi.click();
    const b = [...d.querySelectorAll('#tasti .tasto')].find(x => x.textContent.trim() === 'Mozzarella');
    b.click();
    const n = d.querySelectorAll('.prezzo-riga').length;
    console.log(`  «Mozzarella» acceso dal cassetto → ${n} prezzi`);
    if (!n) guai.push('«Mozzarella» acceso dal cassetto non mostra prezzi');
  }

  if (errori.length) guai.push('errori in pagina: ' + errori.join(' | '));
  if (guai.length) { console.log('\nNON VA:'); guai.forEach(g => console.log('  ✗ ' + g)); process.exit(1); }
  console.log('  il cassetto fa quello che deve');
  process.exit(0);
}, 2500);
