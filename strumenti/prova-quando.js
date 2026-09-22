/* Controlla che le offerte non ancora cominciate non si spaccino per offerte
   di oggi: devono portare il bollo «vale dal ...» e non prendersi mai il bollo
   «il meno caro», che spetta al meno caro FRA QUELLI CHE VALGONO OGGI.

   Serve perche i volantini nuovi si leggono in anticipo. Il 2026-09-05 sono
   entrati quelli dell'Eurospin (dal 10) e dell'MD (dall'8): senza questo
   Manlio leggerebbe come prezzo migliore uno che in cassa non gli fanno.

   ATTENZIONE, LA REGOLA E CAMBIATA IL 2026-09-05. Prima le offerte future
   venivano spinte in fondo all'elenco e questa prova lo pretendeva. Manlio ha
   chiesto il contrario — «dovrebbero proprio essere in ordine di prezzo» — e
   adesso l'elenco e in ordine di prezzo e basta. Quindi qui si controllano
   due cose diverse da prima:
     1. l'elenco e in ordine di prezzo crescente, senza eccezioni;
     2. il bollo verde «il meno caro» sta sull'offerta meno cara che vale
        oggi, che con l'ordine nuovo puo non essere la prima riga.
   Il posto nell'elenco non dice piu niente sulle date: lo dice il bollo.

       node prova-quando.js out/sito.html
       node prova-quando.js out/sito.html 2026-09-07   (fingendo un altro giorno)

   Il secondo modo serve a provare la cosa piu difficile da vedere: la pagina
   decide scaduto e «non ancora» a ogni apertura, contro la data di chi guarda.
   Cosi una pagina lasciata li una settimana non spaccia per buone offerte
   finite nel frattempo. Fingendo il giorno si controlla che sia vero davvero. */
const fs = require('fs');
const { JSDOM, VirtualConsole } = require('jsdom');
const errori = [];
const finto = process.argv[3];            // «2026-09-07», facoltativo
const dom = new JSDOM(fs.readFileSync(process.argv[2], 'utf8'), {
  runScripts: 'dangerously', pretendToBeVisual: true,
  url: 'https://manliograndi-del.github.io/spesa-a/',
  beforeParse(w) {
    if (!finto) return;
    const Vero = w.Date;
    // basta il giorno: la pagina chiede solo new Date().toLocaleDateString('sv')
    function Finta(...a) { return a.length ? new Vero(...a) : new Vero(finto + 'T12:00:00'); }
    Finta.prototype = Vero.prototype;
    Finta.now = () => new Vero(finto + 'T12:00:00').getTime();
    w.Date = Finta;
  },
  virtualConsole: new VirtualConsole().on('jsdomError', e => errori.push(String(e.detail || e.message).split('\n')[0])),
});
setTimeout(() => {
  const d = dom.window.document;
  const guai = [];
  let visti = 0, futuri = 0;
  for (const b of [...d.querySelectorAll('.tasto')].filter(x => !x.classList.contains('agg'))) {
    const nome = b.textContent.trim();
    b.click();
    const righe = [...d.querySelectorAll('.prezzo-riga')].map(r => ({
      dopo: /vale dal|vale dall/.test(r.textContent),
      meno: !!r.querySelector('.bollo.meno'),
      // «12,45 €» -> 12.45. E il numero grande a destra, quello per unita.
      val: parseFloat(r.querySelector('.val .n').textContent
                       .replace(/[^0-9,.]/g, '').replace(',', '.')),
    }));
    visti += righe.length;
    futuri += righe.filter(r => r.dopo).length;

    // 1. in ordine di prezzo, senza eccezioni.
    for (let i = 1; i < righe.length; i++)
      if (righe[i].val < righe[i - 1].val - 0.001) {
        guai.push(`«${nome}»: riga ${i + 1} costa ${righe[i].val} e sta sotto una da ${righe[i - 1].val}`);
        break;
      }

    // 2. il bollo verde sta sul meno caro CHE VALE OGGI, e su nessun altro.
    const attesa = righe.findIndex(r => !r.dopo);
    righe.forEach((r, i) => {
      if (r.meno && i !== attesa)
        guai.push(`«${nome}»: il bollo «il meno caro» sta sulla riga ${i + 1}`
                  + (r.dopo ? ', che non vale ancora' : `, ma il meno caro di oggi e la ${attesa + 1}`));
      if (!r.meno && i === attesa)
        guai.push(`«${nome}»: la riga ${i + 1} e il meno caro di oggi e non ha il bollo`);
    });
  }
  console.log('  giorno: ' + (finto || 'oggi'));
  // ogni riga deve dire quanto dura: i volantini durano periodi diversi
  const senzaDurata = [...d.querySelectorAll('.prezzo-riga')]
    .filter(r => !/fino al |vale dal|vale dall/.test(r.querySelector('.sotto').textContent));
  if (senzaDurata.length)
    guai.push(`${senzaDurata.length} righe non dicono fino a quando valgono`);
  console.log(`  righe guardate: ${visti}, di cui non ancora valide: ${futuri}`);
  const segnati = f => [...d.querySelectorAll('#vol li')]
    .filter(li => f.test(li.textContent))
    .map(li => li.querySelector('.i').textContent + ' ' + li.querySelector('.p').textContent.split('—')[0].trim());
  console.log('  «non ancora cominciato»: ' + (segnati(/non ancora cominciato/).join(' · ') || 'nessuno'));
  console.log('  «scaduto»: ' + (segnati(/— scaduto/).join(' · ') || 'nessuno'));
  if (errori.length) guai.push('errori in pagina: ' + errori.join(' | '));
  if (guai.length) {
    console.log('\nNON VA:'); guai.forEach(g => console.log('  ✗ ' + g));
    process.exit(1);
  }
  console.log('  in ordine di prezzo, e «il meno caro» e comprabile oggi');
  process.exit(0);
}, 2500);
