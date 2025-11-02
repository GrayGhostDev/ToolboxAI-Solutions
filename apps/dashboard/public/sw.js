// Service Worker - Unregistration Script
// This file ensures any previously registered service workers are unregistered
// Service worker functionality is currently disabled for this application

self.addEventListener('install', function(event) {
  // Skip waiting to activate immediately
  self.skipWaiting();
});

self.addEventListener('activate', function(event) {
  console.log('Service Worker: Unregistering...');

  event.waitUntil(
    // Clear all caches
    caches.keys()
      .then(function(cacheNames) {
        return Promise.all(
          cacheNames.map(function(cacheName) {
            console.log('Service Worker: Deleting cache:', cacheName);
            return caches.delete(cacheName);
          })
        );
      })
      .then(function() {
        // Unregister this service worker
        return self.registration.unregister();
      })
      .then(function() {
        console.log('Service Worker: Successfully unregistered');
        // Take control and reload all clients
        return self.clients.claim();
      })
      .then(function() {
        // Notify all clients to reload
        return self.clients.matchAll().then(function(clients) {
          clients.forEach(function(client) {
            client.postMessage({
              type: 'SW_UNREGISTERED',
              message: 'Service Worker has been unregistered. Please reload the page.'
            });
          });
        });
      })
  );
});

// Minimal fetch handler - pass through all requests
self.addEventListener('fetch', function(event) {
  // Don't handle any fetch events - just pass through
  return;
});

