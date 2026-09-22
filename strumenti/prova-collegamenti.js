const fs = require('fs');
const { JSDOM, VirtualConsole } = require('jsdom');
const file = process.argv[2];
const errori = [];
const dom = new JSDOM(fs.readFileSync(file, 'utf8'), {
  runScripts: 'dangerously', pretendToBeVisual: true,
  url: 'https://manliograndi-del.github.io/spesa-a/',
  virtualConsole: new VirtualConsole().on('jsdomError', e => errori.push(String(e.detail || e.message).split('\n')[0])),
});
setTimeout(() => {
  const d = dom.window.document, ris = d.getElementById('risultato');
  const tasti = [...d.querySelectorAll('#tasti .tasto')].filter(b => !b.classList.contains('agg'));
  const tutti = new Set();
  let senza = 0, righe = 0;
  for (const b of tasti) {
    b.dispatchEvent(new dom.window.MouseEvent('click', { bubbles: true }));
    for (const r of ris.querySelectorAll('.prezzo-riga')) {
      righe++;
      const a = r.querySelector('a.dove');
      if (a) tutti.add(a.href); else if (!/non individuata/.test(r.textContent)) senza++;
    }
    for (const a of ris.querySelectorAll('a.pag-riga')) tutti.add(a.href);
  }
  console.log('righe di prezzo viste:', righe, '| senza collegamento e senza spiegazione:', senza);
  console.log('collegamenti distinti:', tutti.size);
  const brutti = [...tutti].filter(u => !/^https:\/\/(www\.anteprimavolantino\.it|resources\.volantinopiu\.it|eu\.kimbicdn\.com|app\.ekomdiscount\.it)\//.test(u));
  console.log('indirizzi malformati:', brutti.length ? brutti.slice(0,3) : 'nessuno');
  const nuova = [...d.querySelectorAll('a.dove, a.pag-riga')].every(a => a.target === '_blank' && /noopener/.test(a.rel));
  console.log('si aprono in una scheda nuova, in sicurezza:', nuova);
  console.log(errori.length ? 'ERRORI: ' + errori.join(' ;; ') : 'nessun errore');
  fs.writeFileSync('/tmp/link-campione.txt', [...tutti].join('\n'));
  process.exit(0);
}, 2500);
