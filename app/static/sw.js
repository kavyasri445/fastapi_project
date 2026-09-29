const CACHE_NAME = "workflow-system-v3";

const FILES_TO_CACHE = [
    "/",
    "/static/index.html",
    "/signin",
    "/forms-page",
    "/create-form",
    "/form-builder",
    "/manifest.json"
];

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                return Promise.all(
                    FILES_TO_CACHE.map((url) => {
                        return cache.add(url).catch((error) => {
                            console.warn(
                                "Could not cache:",
                                url,
                                error
                            );
                        });
                    })
                );
            })
    );

    self.skipWaiting();
});


self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((cacheName) => cacheName !== CACHE_NAME)
                    .map((cacheName) => caches.delete(cacheName))
            );
        })
    );

    self.clients.claim();
});


self.addEventListener("fetch", (event) => {
    // Only handle GET requests
    if (event.request.method !== "GET") {
        return;
    }

    event.respondWith(
        caches.match(event.request)
            .then((cachedResponse) => {
                if (cachedResponse) {
                    return cachedResponse;
                }

                return fetch(event.request)
                    .then((networkResponse) => {
                        return networkResponse;
                    })
                    .catch(() => {
                        return new Response(
                            "You are offline. Please check your internet connection.",
                            {
                                status: 503,
                                statusText: "Service Unavailable",
                                headers: {
                                    "Content-Type": "text/plain"
                                }
                            }
                        );
                    });
            })
    );
});