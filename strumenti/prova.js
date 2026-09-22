/* Apre la pagina in un browser finto e controlla che faccia quello che deve.
   Serve perche i due guasti peggiori (uno script chiuso a meta da un commento,
   e un pezzo che partiva prima che la lista esistesse) non si vedevano ne
   rileggendo il codice ne controllando la sintassi: la pagina usciva bella e
   muta. Questo la apre, clicca i bottoni e guarda se escono i prezzi.

       cd /tmp/dom && node .../prova.js <file.html>   (serve: npm install jsdom) */
const fs = require('fs');
const { JSDOM, VirtualConsole } = require('jsdom');

const file = process.argv[2];
const errori = [];
const vc = new VirtualConsole()
  .on('jsdomError', e => errori.push(String(e.detail && e.detail.stack || e.message).split('\n').slice(0,3).join(' | ')))
  .on('error', (...a) => errori.push('console.error: ' + a.join(' ')));

const dom = new JSDOM(fs.readFileSync(file, 'utf8'),
  { runScripts: 'dangerously', pretendToBeVisual: true, virtualConsole: vc,
    url: 'https://manliograndi-del.github.io/spesa-a/' });

setTimeout(() => {
  const d = dom.window.document;
  const tasti = [...d.querySelectorAll('#tasti .tasto')].filter(b => !b.classList.contains('agg'));
  const ris = d.getElementById('risultato');
  let male = 0;

  const dimmi = (ok, testo) => { console.log(`  ${ok ? '·' : 'MALE'} ${testo}`); if (!ok) male++; };

  console.log(file.split('/').pop());
  dimmi(errori.length === 0, errori.length ? 'errori: ' + errori.join(' ;; ') : 'nessun errore');
  dimmi(tasti.length > 0, `${tasti.length} bottoni dei prodotti`);
  dimmi(ris && ris.querySelectorAll('.prezzo-riga').length > 0,
        `${ris ? ris.querySelectorAll('.prezzo-riga').length : 0} righe di prezzo al primo sguardo`);

  // clicco ogni bottone e pretendo prezzi o almeno pagine da guardare
  for (const b of tasti) {
    errori.length = 0;
    b.dispatchEvent(new dom.window.MouseEvent('click', { bubbles: true }));
    const prezzi = ris.querySelectorAll('.prezzo-riga').length;
    const pagine = ris.querySelectorAll('.pag-riga').length;
    dimmi(errori.length === 0 && (prezzi > 0 || pagine > 0),
          `«${b.textContent}»: ${prezzi} prezzi, ${pagine} pagine` +
          (errori.length ? ' — ' + errori.join(' ;; ') : ''));
  }
  console.log(male ? `  ${male} cose non vanno\n` : '  tutto a posto\n');
  process.exit(male ? 1 : 0);
}, 2500);
