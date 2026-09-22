/* LA FINESTRA DELLE NOVITÀ DELLA PAGINA, chiesta da Manlio il 2026-09-18:
   «la prima volta che uno apre la pagina sarebbe carino che ci fosse una
   finestra novità, a partire dalla casella di ricerca; sono novità
   nell'interfaccia e nelle possibilità, non nei prodotti».

   Qui si controllano le cose che, rompendosi, non si vedono rileggendo:
   - la finestra si apre DA SOLA la prima volta, e dentro c'e almeno la
     casella di ricerca, che e da li che Manlio voleva partire;
   - NON parla di prezzi: se ci finisse dentro un'offerta, questa finestra
     diventerebbe un doppione del diario e invecchierebbe da sola;
   - chiusa una volta NON torna piu (e la differenza fra un benvenuto e una
     seccatura), e nemmeno chiudendola col buio intorno;
   - una novita nuova, arrivata dopo, la fa tornare con dentro SOLO quella;
   - sta fuori dalla barra appiccicata, come il cassetto e la ricerca.        */
const fs = require('fs');
const { JSDOM, VirtualConsole } = require('jsdom');
const file = process.argv[2] || 'out/sito.html';
const testo = fs.readFileSync(file, 'utf8');
const male = [];

const errori = [];
const vc = new VirtualConsole().on('jsdomError',
  e => errori.push(String(e.detail || e.message).split('\n')[0]));
const dom = new JSDOM(testo, {
  runScripts: 'dangerously', pretendToBeVisual: true, virtualConsole: vc,
  url: 'https://manliograndi-del.github.io/spesa-a/',
});

setTimeout(() => {
  const w = dom.window, d = w.document;
  if (errori.length) male.push('errori nella pagina: ' + errori.join(' / '));

  const buio = d.getElementById('buio');
  if (!buio) { console.error('MANCA la finestra delle novità'); process.exit(1); }
  if (buio.hidden) male.push('la finestra non si apre alla prima apertura');
  if (d.querySelector('.barra').contains(buio))
    male.push('LA FINESTRA STA DENTRO LA BARRA: si ripianta come il cassetto');

  const voci = [...d.querySelectorAll('#voci-novita .voce')];
  if (voci.length < 3) male.push('le novità elencate sono solo ' + voci.length);
  voci.forEach(v => {
    if (!v.querySelector('.quando').textContent.trim()) male.push('una novità senza data');
    if (!v.querySelector('h3').textContent.trim()) male.push('una novità senza titolo');
    if (v.querySelector('p').textContent.trim().length < 20) male.push('una novità senza spiegazione');
  });

  const dentro = d.querySelector('.finestra').textContent;
  if (!/[Cc]erca fra i prezzi/.test(dentro))
    male.push('la finestra non parte dalla casella di ricerca, che è quello che ha chiesto');
  /* NIENTE PREZZI QUI DENTRO: le novità dei prezzi hanno il loro tasto. */
  if (/€|\d+,\d\d\b/.test(dentro))
    male.push('C\'È UN PREZZO nella finestra: qui vanno solo le novità della pagina');
  if (!/Novità/.test(dentro))
    male.push('la finestra non dice dove stanno invece le novità dei prezzi');

  /* «Ho capito»: si chiude e non torna. */
  d.getElementById('chiudi-novita').dispatchEvent(new w.Event('click'));
  if (!buio.hidden) male.push('«Ho capito» non chiude la finestra');
  w.eval('mostraNovita()');
  if (!buio.hidden) male.push('la finestra torna anche dopo che uno l\'ha già vista');

  /* Una novità nuova deve farla tornare, e da sola. */
  w.eval("DATI.novita.push({id:'2099-01-01-prova',quando:'domani',titolo:'Cosa nuova',"
         + "testo:'Una cosa nuova arrivata dopo, che deve comparire da sola.'}); mostraNovita()");
  if (buio.hidden) {
    male.push('una novità nuova non fa tornare la finestra');
  } else {
    const dopo = [...d.querySelectorAll('#voci-novita .voce')];
    if (dopo.length !== 1)
      male.push('tornando, la finestra rimostra anche le vecchie (' + dopo.length + ' voci)');
  }

  /* Il buio intorno chiude; toccare dentro la finestra no. */
  d.querySelector('.finestra').dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  if (buio.hidden) male.push('toccando dentro la finestra si chiude');
  buio.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  if (!buio.hidden) male.push('il buio intorno non chiude la finestra');

  if (male.length) { male.forEach(x => console.error('  ✗ ' + x)); process.exit(1); }
  console.log('  novità elencate: ' + voci.length
              + ' (' + voci.map(v => v.querySelector('h3').textContent).join(' · ') + ')');
  console.log('  si apre una volta sola, non parla di prezzi, sta fuori dalla barra');
  process.exit(0);
}, 1500);
