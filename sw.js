/* Service worker della Spesa.

   Tiene la pagina disponibile in negozio, dove il segnale è pessimo.

   Dal 2026-09-04 la Spesa ha un sito tutto suo: prima stava dentro quello
   della Palestra e questo file serviva anche a difendersi dal service worker
   della Palestra, che dall'alto senza rete serviva la sua pagina al posto
   della nostra. Adesso qui sopra non c'è più nessuno.

   Alza il numero a ogni rilascio, altrimenti resta in giro la copia vecchia. */
const PREFISSO = "spesa-a-";
const CACHE = PREFISSO + "v48";
const FILE = ["./", "./index.html", "./novita.html", "./manifest.webmanifest",
              "./icon-192.png", "./icon-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE)
      .then((c) => Promise.all(FILE.map((f) => c.add(f).catch(() => null))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((k) => Promise.all(k
        .filter((x) => x.indexOf(PREFISSO) === 0 && x !== CACHE)
        .map((x) => caches.delete(x))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  /* Quello che non è di casa nostra non ci riguarda: i caratteri di Google
     se non arrivano fanno solo scendere ai caratteri di sistema. */
  if (new URL(e.request.url).origin !== self.location.origin) return;

  /* La pagina prima alla rete: i prezzi cambiano ogni settimana e servirla
     dalla cache vorrebbe dire mostrare offerte scadute. Senza rete si ricade
     sulla copia salvata, che è meglio di niente. */
  if (e.request.mode === "navigate" || e.request.destination === "document") {
    e.respondWith(
      fetch(e.request)
        .then((res) => {
          const copia = res.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copia)).catch(() => {});
          return res;
        })
        .catch(() => caches.match(e.request).then((r) => r || caches.match("./index.html")))
    );
    return;
  }

  e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
});
