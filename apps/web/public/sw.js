/* FlashFacts Service Worker - Offline Fact Jumper Coordinator */
const CACHE_NAME = 'flashfacts-offline-v2';

const PRECACHE_ASSETS = [
  '/offline.html',
  '/fact-jumper',
  '/favicon.ico',
  '/globe.svg',
  '/file.svg'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      // Pre-cache essential offline assets
      return cache.addAll(PRECACHE_ASSETS).catch((err) => {
        // Individual precache failures shouldn't break install
        console.warn('[SW] Some precache assets failed:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log('[SW] Deleting obsolete cache:', key);
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // 1. Never cache non-GET requests
  if (req.method !== 'GET') {
    return;
  }

  // 2. Never cache private API endpoints or auth tokens
  if (url.pathname.startsWith('/api/') || url.pathname.includes('/auth/')) {
    return;
  }

  // 3. Navigation requests (Page reloads, link clicks, direct visits)
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req).then((networkRes) => {
        // If user is on /fact-jumper while online, update its cache
        if (networkRes.ok && url.pathname === '/fact-jumper') {
          const clone = networkRes.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, clone));
        }
        return networkRes;
      }).catch(async () => {
        // Network failed -> Serve offline fallback
        const cache = await caches.open(CACHE_NAME);

        // Check if the exact route was cached
        const cachedRoute = await cache.match(req);
        if (cachedRoute) {
          return cachedRoute;
        }

        // Check if the offline shell is cached
        const offlineShell = await cache.match('/offline.html');
        if (offlineShell) {
          return offlineShell;
        }

        // Scenario 4: First visit without previously cached files
        return new Response(
          `<!DOCTYPE html>
          <html lang="en">
          <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>FlashFacts — Offline Notice</title>
            <style>
              body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0F172A; color: #F8FAFC; display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; text-align: center; }
              .card { background: #1E293B; border: 1px solid #334155; border-radius: 16px; padding: 32px; max-width: 480px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3); }
              h1 { font-size: 1.4rem; color: #F59E0B; margin-bottom: 12px; }
              p { font-size: 0.95rem; line-height: 1.6; color: #94A3B8; margin-bottom: 24px; }
              button { background: #2563EB; color: #fff; font-weight: 600; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 0.9rem; }
              button:hover { background: #1D4ED8; }
            </style>
          </head>
          <body>
            <div class="card">
              <h1>⚡ Offline Game Not Cached Yet</h1>
              <p>FlashFacts Fact Jumper has not finished caching on this device. Please connect to the internet and open FlashFacts once so the offline runner can be prepared.</p>
              <button onclick="window.location.reload()">Retry Connection</button>
            </div>
          </body>
          </html>`,
          {
            status: 503,
            headers: { 'Content-Type': 'text/html; charset=utf-8' }
          }
        );
      })
    );
    return;
  }

  // 4. Next.js Static Chunks & Public Assets (Cache-First / Stale-While-Revalidate)
  if (url.pathname.startsWith('/_next/static/') || url.pathname.endsWith('.svg') || url.pathname.endsWith('.ico')) {
    event.respondWith(
      caches.open(CACHE_NAME).then((cache) => {
        return cache.match(req).then((cachedResponse) => {
          if (cachedResponse) {
            // Update in background if online
            fetch(req).then((networkRes) => {
              if (networkRes.ok) cache.put(req, networkRes);
            }).catch(() => {});
            return cachedResponse;
          }
          return fetch(req).then((networkRes) => {
            if (networkRes.ok) {
              cache.put(req, networkRes.clone());
            }
            return networkRes;
          });
        });
      })
    );
  }
});
