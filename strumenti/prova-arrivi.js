/* Rifà il caso di Manlio: un telefono con una lista salvata a cui mancano i
   prodotti aggiunti dopo, più uno suo. Devono arrivare i mancanti, restare il
   suo, e un prodotto tolto apposta NON deve tornare al giro dopo. */
const fs = require('fs');
const { JSDOM, VirtualConsole } = require('jsdom');
const html = fs.readFileSync(process.argv[2], 'utf8');
const SUA = [
  'Carne di bue','Tonno','Salmone','Suino','Pollo','Formaggio','Uova',"Olio d'oliva",'Dentifricio'
].map(n => ({ nome: n, parole: [n.toLowerCase()], cat: n === 'Dentifricio' ? null : n }));
const memoria = { 'spesa.lista.v1': JSON.stringify(SUA) };

function apri(dopo) {
  return new Promise(res => {
    const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true,
      url: 'https://manliograndi-del.github.io/spesa-a/', virtualConsole: new VirtualConsole(),
      beforeParse(w) {
        Object.defineProperty(w, 'localStorage', { value: {
          getItem: k => (k in memoria ? memoria[k] : null),
          setItem: (k, v) => { memoria[k] = String(v); },
          removeItem: k => { delete memoria[k]; }, clear: () => {},
        }});
      }});
    setTimeout(() => {
      const d = dom.window.document;
      if (dopo) dopo(d, dom.window);
      res({ tasti: [...d.querySelectorAll('.tasto')].filter(b => !b.classList.contains('agg'))
              .map(b => b.textContent.trim()),
            avviso: (d.getElementById('stato-lista') || {}).textContent });
    }, 2500);
  });
}

(async () => {
  const a = await apri();
  console.log('1° apertura  → ' + a.tasti.join(' · '));
  console.log('   avviso: ' + a.avviso);
  const b = await apri();
  console.log('2° apertura  → ' + b.tasti.join(' · '));
  console.log('   avviso: ' + b.avviso);
  // adesso ne toglie uno apposta
  const c = await apri((d, w) => {
    [...d.querySelectorAll('.tasto')].find(x => x.textContent.trim() === 'Marmellata').click();
    // dal 2026-09-05 si toglie con la crocetta accanto al nome, e va confermato
    d.querySelector('.capo .elimina').click();
    d.querySelector('.conferma .si').click();
  });
  console.log('tolta Marmellata → ' + c.tasti.join(' · '));
  const e = await apri();
  console.log('3° apertura  → ' + e.tasti.join(' · '));
  const guai = [];
  if (!['Biscotti','Yogurt','Marmellata','Cioccolato'].every(n => a.tasti.includes(n)))
    guai.push('i quattro prodotti nuovi non sono arrivati');
  if (!a.tasti.includes('Dentifricio')) guai.push('«Dentifricio», che è suo, è sparito');
  if (a.tasti.length !== b.tasti.length) guai.push('la seconda apertura non ha la stessa lista');
  if (e.tasti.includes('Marmellata')) guai.push('«Marmellata», tolta apposta, è tornata');
  if (guai.length) { console.log('\nNON VA:'); guai.forEach(g => console.log('  ✗ ' + g)); process.exit(1); }
  console.log('\ntutto a posto: i nuovi arrivano, i suoi restano, i tolti non tornano');
})();
