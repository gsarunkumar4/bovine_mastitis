/* ==========================================================================
   MastiSense Service Worker — Progressive Web Application (§1)
   Provides offline application shell caching and network-first API requests.
   ========================================================================== */

const CACHE_NAME = "mastisense-v1.2";
const STATIC_ASSETS = [
  "./",
  "./index.html",
  "./styles.css",
  "./app.js",
  "./manifest.json",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "https://cdn.jsdelivr.net/npm/chart.js",
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
];

// Install: pre-cache application shell assets
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn("[SW] Non-critical cache failure:", err);
      });
    }).then(() => self.skipWaiting())
  );
});

// Activate: clean up outdated caches
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch: Network-first with cache fallback for dynamic API calls;
// Cache-first with network revalidation for static assets.
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Skip non-GET requests and SSE event streams
  if (event.request.method !== "GET" || url.pathname.includes("/events/stream")) {
    return;
  }

  // Static shell assets -> Stale-While-Revalidate
  if (
    url.origin === location.origin &&
    (url.pathname.endsWith(".css") ||
      url.pathname.endsWith(".js") ||
      url.pathname.endsWith(".html") ||
      url.pathname.endsWith(".png") ||
      url.pathname === "/" ||
      url.pathname.endsWith("/"))
  ) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        const fetchPromise = fetch(event.request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const copy = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          }
          return networkResponse;
        }).catch(() => cached);

        return cached || fetchPromise;
      })
    );
    return;
  }

  // API calls -> Network-first with cache fallback
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response && response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => {
        return caches.match(event.request).then((cached) => {
          if (cached) return cached;
          // Return offline JSON if API call
          if (event.request.headers.get("accept")?.includes("application/json")) {
            return new Response(
              JSON.stringify({
                offline: true,
                message: "MastiSense is running in offline mode. Cached data displayed if available."
              }),
              { headers: { "Content-Type": "application/json" } }
            );
          }
          return caches.match("./index.html");
        });
      })
  );
});
