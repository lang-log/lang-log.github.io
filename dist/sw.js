// Lang Log's service worker (.claude/rules/pwa.md), registered by dist/pwa.js.
// It keeps a copy of every page and file of the site that the visitor opens, so they open
// again offline. The whole site is far too large to download in advance, so nothing is
// stored that the visitor has not opened, except the top page.
// - Pages, data and other files: from the network first, so a visitor online always sees
//   the current version; the stored copy is used only when the network fails.
// - Files with ?v=<content hash> (tools/version_assets.py): never change at that address,
//   so the stored copy is used first.
// - The whole site is offered as a download on GitHub Releases instead (.claude/rules/pwa.md).
//   A copy stored by the earlier "save the whole site" button is deleted on activate, with
//   every other cache but CACHE.
// - Only requests to this site, inside this worker's scope. Other sites (huggingface.co)
//   are left to the browser.
'use strict';

// Change CACHE_VERSION when the way files are stored changes; the old cache is then deleted.
var CACHE_VERSION = 1;
var CACHE = 'lang-log-' + CACHE_VERSION;
// At most this many stored responses; the oldest go first. Bounds the space the site takes
// on a visitor's device (a record page with its data and map is about ten files).
var MAX_ENTRIES = 1000;
var SCOPE = new URL(self.registration.scope);
var START = new URL('./', SCOPE).href;

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches
      .open(CACHE)
      .then(function (cache) {
        return cache.add(START);
      })
      .then(function () {
        return self.skipWaiting();
      }),
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches
      .keys()
      .then(function (names) {
        return Promise.all(
          names
            .filter(function (name) {
              return name !== CACHE;
            })
            .map(function (name) {
              return caches.delete(name);
            }),
        );
      })
      .then(function () {
        return self.clients.claim();
      }),
  );
});

function handled(request) {
  if (request.method !== 'GET') return false;
  var url = new URL(request.url);
  return url.origin === SCOPE.origin && url.pathname.indexOf(SCOPE.pathname) === 0;
}

function trim(cache) {
  return cache.keys().then(function (keys) {
    return Promise.all(
      keys.slice(0, Math.max(0, keys.length - MAX_ENTRIES)).map(function (key) {
        return cache.delete(key);
      }),
    );
  });
}

function store(request, response) {
  if (response.ok && response.type === 'basic') {
    var copy = response.clone();
    caches.open(CACHE).then(function (cache) {
      return cache.put(request, copy).then(function () {
        return trim(cache);
      });
    });
  }
  return response;
}

function fromNetwork(request) {
  return fetch(request).then(function (response) {
    return store(request, response);
  });
}

// The stored copy of a request, when the network fails. A page address with a query
// (q?q=..., signs-and-scripts.html?domain=sign) draws its content with scripts, so the copy
// without the query serves too.
function stored(request, error) {
  return caches.match(request).then(function (exact) {
    return (
      exact ||
      caches.match(request, { ignoreSearch: true }).then(function (any) {
        if (any) return any;
        throw error;
      })
    );
  });
}

function networkFirst(request) {
  return fromNetwork(request).catch(function (error) {
    return stored(request, error);
  });
}

function cacheFirst(request) {
  return caches.match(request).then(function (exact) {
    return (
      exact ||
      fromNetwork(request).catch(function (error) {
        return stored(request, error);
      })
    );
  });
}

self.addEventListener('fetch', function (event) {
  var request = event.request;
  if (!handled(request)) return;
  var versioned = new URL(request.url).searchParams.has('v');
  event.respondWith(versioned ? cacheFirst(request) : networkFirst(request));
});
