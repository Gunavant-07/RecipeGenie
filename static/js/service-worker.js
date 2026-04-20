// service-worker.js
// Smart Recipe Recommendation System - PWA Service Worker
// Version: 1.0.0 - January 2026

const CACHE_NAME = 'recipegenie-v2';
const OFFLINE_PAGE = '/offline.html'; // Optional custom offline page

// List of assets to cache immediately on install
const STATIC_ASSETS = [
  '/',
  '/static/css/style.css',
  '/static/js/app.js',
];

async function cacheAvailableAssets(cache) {
  const results = await Promise.allSettled(
    STATIC_ASSETS.map(async (asset) => {
      const response = await fetch(asset, { cache: 'reload' });
      if (!response.ok) {
        throw new Error(`${asset} returned ${response.status}`);
      }
      await cache.put(asset, response);
      return asset;
    })
  );

  results
    .filter(result => result.status === 'rejected')
    .forEach(result => console.warn('[Service Worker] Skipped cache asset:', result.reason));
}

// Install event - cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Service Worker] Pre-caching static assets');
      return cacheAvailableAssets(cache);
    }).catch(err => {
      console.error('[Service Worker] Install failed:', err);
    })
  );

  // Skip waiting so new service worker activates immediately
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[Service Worker] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );

  // Take control of all open clients immediately
  self.clients.claim();
});

// Fetch event - Cache-first for static, Network-first for API/dynamic
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Skip cross-origin requests or non-GET requests
  if (event.request.method !== 'GET' || url.origin !== self.location.origin) {
    event.respondWith(fetch(event.request));
    return;
  }

  // API calls → Network-first, fallback to cache only if offline
  if (url.pathname.startsWith('/api/') || url.pathname.includes('/recommend') || url.pathname.includes('/cooked') || url.pathname.includes('/history')) {
    event.respondWith(
      fetch(event.request)
        .then((networkResponse) => {
          // Clone and cache successful responses
          if (networkResponse && networkResponse.status === 200) {
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, responseToCache);
            });
          }
          return networkResponse;
        })
        .catch(() => {
          // Offline → return cached response if available
          return caches.match(event.request).then((cachedResponse) => {
            return cachedResponse || new Response('Offline - API unavailable', {
              status: 503,
              statusText: 'Service Unavailable',
              headers: { 'Content-Type': 'text/plain' }
            });
          });
        })
    );
    return;
  }

  // Static assets → Cache-first
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }

      // Not in cache → fetch from network
      return fetch(event.request).then((networkResponse) => {
        if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
          return networkResponse;
        }

        // Cache the new response
        const responseToCache = networkResponse.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseToCache);
        });

        return networkResponse;
      }).catch(() => {
        // Offline fallback (optional custom offline page)
        return caches.match(OFFLINE_PAGE).then((offlineResponse) => {
          return offlineResponse || new Response('RecipeGenie is offline. Please reconnect and try again.', {
            status: 503,
            statusText: 'Service Unavailable',
            headers: { 'Content-Type': 'text/plain' }
          });
        });
      });
    })
  );
});

// Optional: Background Sync (stub - can be expanded later)
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-cooked-recipes') {
    event.waitUntil(syncCookedRecipes());
  }
});

async function syncCookedRecipes() {
  console.log('[Service Worker] Background sync - sending pending cooked actions');
  // You would implement IndexedDB queue here and send to /cooked endpoint
}

// Optional: Push notifications (stub)
self.addEventListener('push', (event) => {
  const data = event.data.json();
  const options = {
    body: data.body || 'New Gujarati recipe recommendation!',
    icon: '/static/images/icon-192.png',
    badge: '/static/images/icon-192.png'
  };
  event.waitUntil(self.registration.showNotification('Gujarat Recipe AI', options));
});
