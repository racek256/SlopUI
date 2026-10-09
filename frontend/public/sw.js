// Barebones service worker — fill in caching strategy as needed.
// Currently: install + activate only, no fetch interception (passthrough).

const CACHE_NAME = 'TODO-app-cache-v1';
const PRECACHE_URLS = [
  // TODO: add URLs to precache, e.g. '/', '/index.html', '/manifest.webmanifest'
];

self.addEventListener('install', (event) => {
  // TODO: event.waitUntil(caches.open(CACHE_NAME).then((c) => c.addAll(PRECACHE_URLS)))
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  // TODO: cleanup old caches
  event.waitUntil(self.clients.claim());
});

// TODO: add fetch handler when you want offline support, e.g.:
// Minimal fetch passthrough so the SW counts as installed (required for install prompt).
self.addEventListener('fetch', (event) => {
  // TODO: replace with cache-first / network-first strategy
  event.respondWith(fetch(event.request));
});
