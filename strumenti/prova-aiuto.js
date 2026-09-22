/* IL TASTO «AIUTO» E LA SUA FINESTRA, chiesti da Manlio il 2026-09-21: «fammi
   una piccola finestra di help, la metti con un pulsantino con scritto sopra
   aiuto di fianco a quello di novità». Il testo l'ha letto e approvato prima.

   Qui si controllano le cose che, rompendosi, non si vedono rileggendo:
   - il tasto c'è, sta in cima accanto a «Novità» e NON dentro la barra
     appiccicata (la lezione del cassetto: dentro, il telefono si pianta);
   - la finestra NON si apre da sola — quella che si apre da sola è un'altra,
     «Cosa c'è di nuovo», e due finestre addosso all'apertura sarebbero una
     porta sbarrata;
   - si riapre quante volte si vuole: un aiuto che si vede una volta sola non
     è un aiuto;
   - le due finestre non stanno aperte insieme;
   - dentro c'è davvero la spiegazione, non un riquadro vuoto.            */
const fs = require('fs');
const { JSDOM, VirtualConsole } = require('jsdom');
const file = process.argv[2] || 'out/sito.html';
const male = [];
const errori = [];
const dom = new JSDOM(fs.readFileSync(file, 'utf8'), {
  runScripts: 'dangerously', pretendToBeVisual: true,
  url: 'https://manliograndi-del.github.io/spesa-a/',
  virtualConsole: new VirtualConsole().on('jsdomError',
    e => errori.push(String(e.detail || e.message).split('\n')[0])),
});

setTimeout(() => {
  const w = dom.window, d = w.document;
  if (errori.length) male.push('errori nella pagina: ' + errori.join(' / '));

  const tasto = d.getElementById('apri-aiuto');
  const buio = d.getElementById('buio-aiuto');
  if (!tasto || !buio) { console.error('MANCA il tasto Aiuto o la sua finestra'); process.exit(1); }
  if (!/aiuto/i.test(tasto.textContent)) male.push('il tasto non dice «Aiuto»');
  if (!d.querySelector('header').contains(tasto)) male.push('il tasto Aiuto non sta in cima');
  const novita = d.querySelector('header .novita');
  if (!novita) male.push('non trovo il tasto «Novità» accanto a cui sta');
  if (d.querySelector('.barra').contains(tasto))
    male.push('IL TASTO STA DENTRO LA BARRA appiccicata');
  if (d.querySelector('.barra').contains(buio))
    male.push('LA FINESTRA STA DENTRO LA BARRA: si ripianta come il cassetto');

  /* All'apertura è aperta SOLO quella delle novità, mai l'aiuto. */
  if (!buio.hidden) male.push('la finestra dell\'aiuto si apre da sola');
  d.getElementById('chiudi-novita').dispatchEvent(new w.Event('click'));

  tasto.dispatchEvent(new w.Event('click'));
  if (buio.hidden) male.push('toccando «Aiuto» non si apre niente');
  const voci = [...buio.querySelectorAll('.voce')];
  if (voci.length < 8) male.push('la finestra ha solo ' + voci.length + ' spiegazioni');
  voci.forEach(v => {
    if (!v.querySelector('h3') || !v.querySelector('h3').textContent.trim())
      male.push('una spiegazione senza titolo');
    if (!v.querySelector('p') || v.querySelector('p').textContent.trim().length < 40)
      male.push('una spiegazione troppo corta per spiegare qualcosa');
  });
  const dentro = buio.textContent;
  ['per unità', 'il meno caro', '+ altri prodotti', 'Cerca fra i prezzi', 'Novità']
    .forEach(x => { if (dentro.indexOf(x) < 0) male.push('l\'aiuto non parla di «' + x + '»'); });

  /* Toccare dentro non chiude, il buio intorno sì. */
  buio.querySelector('.finestra').dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  if (buio.hidden) male.push('toccando dentro la finestra si chiude');
  buio.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  if (!buio.hidden) male.push('il buio intorno non chiude la finestra');

  /* E si riapre: è la differenza con quella delle novità. */
  tasto.dispatchEvent(new w.Event('click'));
  if (buio.hidden) male.push('la finestra dell\'aiuto non si riapre una seconda volta');
  d.getElementById('chiudi-aiuto').dispatchEvent(new w.Event('click'));
  if (!buio.hidden) male.push('«Ho capito» non chiude la finestra');

  /* Una finestra alla volta: aprendo l'aiuto, le novità si chiudono. */
  w.eval("DATI.novita.push({id:'2099-01-01-prova',quando:'domani',titolo:'Prova',"
         + "testo:'Una novità nuova, lunga abbastanza da essere una spiegazione vera.'});"
         + "try { localStorage.removeItem('spesa.novita.v1'); } catch (e) {} mostraNovita()");
  if (d.getElementById('buio').hidden) {
    male.push('non riesco a riaprire le novità per provare che si chiudano');
  } else {
    tasto.dispatchEvent(new w.Event('click'));
    if (!d.getElementById('buio').hidden)
      male.push('aprendo l\'aiuto la finestra delle novità resta aperta');
  }

  if (male.length) { male.forEach(x => console.error('  ✗ ' + x)); process.exit(1); }
  console.log('  «Aiuto» in cima accanto a «Novità», ' + voci.length + ' spiegazioni dentro');
  console.log('  non si apre da sola, si riapre sempre, una finestra alla volta');
  process.exit(0);
}, 1400);
