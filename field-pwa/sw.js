/* Service worker: cachea el shell para que la app abra sin red.
   Sin esto, "offline-first" es una promesa que se rompe al primer tunel. */
const CACHE = 'hub-campo-v1'
const SHELL = ['./', './index.html', './app.js', './manifest.json']

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()))
})

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url)
  // Las llamadas al Hub NUNCA se cachean: la cola en IndexedDB es la que
  // garantiza la entrega, no el cache HTTP.
  if (url.pathname.startsWith('/ingest') || url.pathname.startsWith('/api')) return

  e.respondWith(
    caches.match(e.request).then((r) => r || fetch(e.request).catch(() => caches.match('./index.html'))),
  )
})
