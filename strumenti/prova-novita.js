/* LA PAGINA DELLE NOVITÀ: il riquadro dei volantini aggiornati in cima, i tre
   tasti (oggi / 3 giorni / 7 giorni) e la tabella di tutti i volantini.
   Chiesti da Manlio il 2026-09-19: «sarebbe bene che apparissero prima di
   tutto i volantini aggiornati, così uno sa l'ultimo giorno e l'ultima
   settimana cosa è stato aggiornato... e una tabellina con tutti i
   supermercati e l'intervallo di validità dei loro volantini».

   Qui si controllano le cose che, rompendosi, non si vedono rileggendo:
   - i tre tasti ci sono e cambiano davvero quello che si vede;
   - «In corso adesso» contiene SOLO volantini che valgono oggi e «In arrivo»
     solo quelli che devono ancora cominciare — se uno finisse nel gruppo
     sbagliato, Manlio andrebbe in negozio con un volantino scaduto in mano;
   - nessun volantino compare in due gruppi;
   - ogni riga dice negozio, date e quanto manca;
   - i volantini che non ho ancora letto sono segnati, se no uno crede che i
     loro prezzi ci siano gia.                                               */
const fs = require('fs');
const { JSDOM, VirtualConsole } = require('jsdom');
const file = process.argv[2] || 'out/novita.html';
const male = [];
const errori = [];
const dom = new JSDOM(fs.readFileSync(file, 'utf8'), {
  runScripts: 'dangerously', pretendToBeVisual: true,
  url: 'https://manliograndi-del.github.io/spesa-a/novita.html',
  virtualConsole: new VirtualConsole().on('jsdomError',
    e => errori.push(String(e.detail || e.message).split('\n')[0])),
});

setTimeout(() => {
  const w = dom.window, d = w.document;
  if (errori.length) male.push('errori nella pagina: ' + errori.join(' / '));

  const tasti = [1, 3, 7].map(n => d.getElementById('b-' + n));
  if (tasti.some(t => !t)) { console.error('MANCANO i tasti oggi/3/7'); process.exit(1); }
  if (tasti.filter(t => t.getAttribute('aria-pressed') === 'true').length !== 1)
    male.push('non c\'è esattamente un tasto acceso');

  /* Il riquadro dei volantini aggiornati deve stare PRIMA della tabella e
     prima delle novità dei prezzi: è la prima cosa che ha chiesto. */
  const agg = d.querySelector('.aggiornati');
  const tab = d.querySelector('.tuttivol');
  const dentro = d.getElementById('dentro');
  if (!agg || !tab || !dentro) { console.error('MANCA una delle tre parti'); process.exit(1); }
  const ordine = [...d.querySelectorAll('.aggiornati, .tuttivol, #dentro')];
  if (ordine[0] !== agg) male.push('i volantini aggiornati non sono la prima cosa');
  if (ordine.indexOf(tab) > ordine.indexOf(dentro))
    male.push('la tabella dei volantini sta sotto le novità dei prezzi');
  const dentroAgg = d.getElementById('agg-dentro').textContent.trim();
  if (!dentroAgg) male.push('il riquadro dei volantini aggiornati è vuoto');

  /* I tre tasti devono cambiare qualcosa: si guarda il testo della pagina. */
  const foto = () => d.getElementById('agg-dentro').textContent
                   + '|' + d.getElementById('dentro').textContent;
  const viste = new Set();
  [1, 3, 7].forEach(n => {
    d.getElementById('b-' + n).dispatchEvent(new w.Event('click'));
    if (d.getElementById('b-' + n).getAttribute('aria-pressed') !== 'true')
      male.push('il tasto ' + n + ' non si accende');
    viste.add(foto());
  });
  if (viste.size < 2) male.push('i tre tasti mostrano tutti la stessa cosa');

  /* La tabella: i gruppi e le date. */
  const OGGI = new w.Date().toLocaleDateString('sv');
  const dati = w.eval('TABELLA');
  const righe = g => [...d.querySelectorAll('#tabvol .gruppo')]
    .filter(s => new RegExp(g, 'i').test(s.querySelector('h3').textContent))
    .flatMap(s => [...s.querySelectorAll('tr')]);

  const corso = righe('in corso'), arrivo = righe('in arrivo'), finiti = righe('appena finiti');
  if (!corso.length) male.push('nessun volantino «in corso»: la tabella non serve a niente');
  const nome = tr => tr.querySelector('.chi b').textContent.trim()
                   + (tr.querySelector('.chi .nome').textContent.trim()
                      ? ' — ' + tr.querySelector('.chi .nome').textContent.trim() : '');
  [...corso, ...arrivo, ...finiti].forEach(tr => {
    if (!tr.querySelector('.chi b').textContent.trim()) male.push('una riga senza negozio');
    if (!tr.querySelector('.date').textContent.trim()) male.push('una riga senza date');
    if (!tr.querySelector('.quanto b').textContent.trim()) male.push('una riga senza «quanto manca»');
  });

  /* Un volantino non può stare in due gruppi. */
  const chiavi = tr => nome(tr) + '/' + tr.querySelector('.date').textContent.trim();
  const tutte = [...corso, ...arrivo, ...finiti].map(chiavi);
  if (new Set(tutte).size !== tutte.length)
    male.push('lo stesso volantino compare in due gruppi');

  /* E il gruppo deve dire la verità sulle date: ogni riga porta con sé le
     date intere, perché quelle scritte sono accorciate. */
  corso.forEach(tr => {
    const fino = tr.getAttribute('data-fino'), ini = tr.getAttribute('data-inizio');
    if (fino && fino < OGGI) male.push('«' + nome(tr) + '» è scaduto ma sta fra quelli in corso');
    if (ini && ini > OGGI) male.push('«' + nome(tr) + '» non è ancora cominciato ma sta fra quelli in corso');
  });
  arrivo.forEach(tr => {
    const ini = tr.getAttribute('data-inizio');
    if (!(ini && ini > OGGI)) male.push('«' + nome(tr) + '» è già cominciato ma sta fra quelli in arrivo');
  });
  finiti.forEach(tr => {
    const fino = tr.getAttribute('data-fino');
    if (fino && !(fino < OGGI)) male.push('«' + nome(tr) + '» vale ancora ma sta fra quelli finiti');
  });

  /* Quelli non ancora letti vanno segnati: se no uno crede di avere i prezzi. */
  const daLeggere = dati.filter(v => !v.letto);
  const segnate = [...d.querySelectorAll('#tabvol tr[data-letto="no"]')];
  if (segnate.length !== daLeggere.length)
    male.push('i volantini non ancora letti in tabella sono ' + segnate.length
              + ' invece di ' + daLeggere.length);
  segnate.forEach(tr => {
    if (!tr.querySelector('.nonletto'))
      male.push('«' + nome(tr) + '» non è ancora letto e la tabella non lo dice');
  });

  if (male.length) { male.forEach(x => console.error('  ✗ ' + x)); process.exit(1); }
  console.log('  volantini in tabella: ' + corso.length + ' in corso, '
              + arrivo.length + ' in arrivo, ' + finiti.length + ' appena finiti'
              + (daLeggere.length ? ' (' + daLeggere.length + ' ancora da leggere, segnati)' : ''));
  console.log('  i volantini aggiornati stanno in cima, i tre tasti cambiano davvero');
  process.exit(0);
}, 1200);
