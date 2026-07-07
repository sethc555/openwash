/* OpenWASH service worker — makes the guardrail work OFFLINE after the first visit.
 * Cache-first for the app shell (so a field worker with no signal still gets a verdict);
 * bump CACHE when any cached asset changes. SPDX-License-Identifier: Apache-2.0 */
'use strict';
var CACHE = 'openwash-v2';
var ASSETS = [
  './', './index.html', './guardrail.js', './i18n.js', './qr.svg',
  './manifest.webmanifest', './icon-192.png', './icon-512.png', './apple-touch-icon.png'
];

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(ASSETS); }).then(function () {
    return self.skipWaiting();
  }));
});

self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.map(function (k) { return k === CACHE ? null : caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});

self.addEventListener('fetch', function (e) {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request).then(function (hit) {
      return hit || fetch(e.request).then(function (res) {
        // cache same-origin successful responses so subsequent offline loads work
        if (res && res.ok && new URL(e.request.url).origin === self.location.origin) {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(e.request, copy); });
        }
        return res;
      }).catch(function () { return caches.match('./index.html'); });
    })
  );
});
