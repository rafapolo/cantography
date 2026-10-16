// scripts/build.js rewrites the name with the commit, so every deploy installs a
// new worker and drops the caches of the old one
const V = 'cantography-dev';

const PRECACHE = [
    './',
    './index.html',
    './data/BE.json',
    './data/BE_0.json.gz',
];

self.addEventListener('install', e => {
    self.skipWaiting();
    e.waitUntil(
        // past the browser's HTTP cache (max-age=600 on GitHub Pages): else a visit made
        // minutes before a deploy fills the new cache with the old files, kept a whole deploy
        caches.open(V).then(c => c.addAll(PRECACHE.map(u => new Request(u, { cache: 'reload' }))).catch(() => {}))
    );
});

self.addEventListener('activate', e => {
    e.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== V).map(k => caches.delete(k)))
        )
    );
    self.clients.claim();
});

// keep a copy without letting a full disk turn into an unhandled error
const keep = (e, req, res) => e.waitUntil(caches.open(V).then(c => c.put(req, res)).catch(() => {}));

self.addEventListener('fetch', e => {
    if (e.request.method !== 'GET') return;
    // the base map's tiles, styles and fonts keep their own HTTP caching: copies here
    // grew without end and froze OpenFreeMap's tileset for a whole deploy
    const url = new URL(e.request.url);
    if (url.origin !== location.origin) return;
    // Page: network-first so deploys show up immediately; cache is the offline fallback
    if (e.request.mode === 'navigate') {
        e.respondWith(
            fetch(e.request.url, { cache: 'no-cache', credentials: 'same-origin' }).then(res => {
                if (res.ok) keep(e, e.request, res.clone());
                return res;
            }).catch(() => caches.match(e.request).then(hit => hit || caches.match('./index.html')))
        );
        return;
    }
    // Everything else, data included, is cache-first within a deploy: the cache is
    // named after the commit, so a new deploy fetches each file once again
    e.respondWith(
        caches.match(e.request).then(hit => {
            if (hit) return hit;
            // revalidated (a 304 when unchanged), never the HTTP cache's copy from before the deploy
            return fetch(url.origin === location.origin ? new Request(e.request, { cache: 'no-cache' }) : e.request).then(res => {
                if (res.ok && res.type !== 'opaque') keep(e, e.request, res.clone());
                return res;
            }).catch(() => caches.match(e.request));
        })
    );
});
