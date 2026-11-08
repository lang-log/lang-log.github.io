// Lang Log's service worker (.claude/rules/pwa.md), registered by dist/pwa.js.
// It keeps a copy of every page and file of the site that the visitor opens, so they open
// again offline. The whole site is far too large to download in advance, so nothing is
// stored that the visitor has not opened, except the top page.
// - Pages, data and other files: from the network first, so a visitor online always sees
//   the current version; the stored copy is used only when the network fails.
// - Files with ?v=<content hash> (tools/version_assets.py): never change at that address,
//   so the stored copy is used first.
// - The "save the whole site" button (dist/pwa.js) sends the files of
//   offline-files.json (tools/pwa.py) here in batches; they go into SITE_CACHE, which is
//   never trimmed, each with its content hash, so a second press skips what is current.
// - Only requests to this site, inside this worker's scope. Other sites (huggingface.co)
//   and the pull request previews under the live site (/preview/, written by the shared
//   workflow in research-aide, pages-with-previews.yml) are left to the browser.
'use strict';

// Change CACHE_VERSION when the way files are stored changes; the old cache is then deleted.
var CACHE_VERSION = 1;
var CACHE = 'lang-log-' + CACHE_VERSION;
var SITE_CACHE = 'lang-log-site-' + CACHE_VERSION;
// The response header that holds a stored file's content hash (offline-files.json).
var HASH_HEADER = 'X-Lang-Log-Hash';
// offline-files.json itself is stored last, as the sign that the whole site is saved.
var FILE_LIST = new URL('offline-files.json', self.registration.scope).href;
// At most this many stored responses; the oldest go first. Bounds the space the site takes
// on a visitor's device (a record page with its data and map is about ten files).
var MAX_ENTRIES = 1000;
var SCOPE = new URL(self.registration.scope);
var PREVIEWS = new URL('preview/', SCOPE).pathname;
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
              return name !== CACHE && name !== SITE_CACHE;
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
  return (
    url.origin === SCOPE.origin &&
    url.pathname.indexOf(SCOPE.pathname) === 0 &&
    url.pathname.indexOf(PREVIEWS) !== 0
  );
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
// (q?q=..., signs-and-scripts.html?domain=sign) draws its content with scripts, and the
// whole-site copy holds files without ?v=<hash>, so the copy without the query serves too.
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

// One file of offline-files.json ([address, size, hash]) into SITE_CACHE, unless it is
// there with the same hash.
function saveFile(cache, file) {
  var url = new URL(file[0], SCOPE).href;
  return cache.match(url).then(function (have) {
    if (have && have.headers.get(HASH_HEADER) === file[2]) return;
    return fetch(url, { cache: 'no-cache' }).then(function (response) {
      if (!response.ok) throw new Error(url + ': HTTP ' + response.status);
      var headers = new Headers(response.headers);
      headers.set(HASH_HEADER, file[2]);
      return response.blob().then(function (body) {
        return cache.put(url, new Response(body, { status: response.status, headers: headers }));
      });
    });
  });
}

// Messages from dist/pwa.js; each answers on the port it came with.
//   { status: true }            -> { saved: whether the whole site is stored }
//   { previous: true }          -> the list stored by the last finished save, or null
//   { save: [files] }           -> { ok } once every file of the batch is stored
//   { finish: list text }       -> drops files the previous list had and this one lacks,
//                                  then stores the list itself
var ACTIONS = {
  status: function () {
    return caches.open(SITE_CACHE).then(function (cache) {
      return cache.match(FILE_LIST).then(function (list) {
        return { saved: !!list };
      });
    });
  },
  previous: function () {
    return caches.open(SITE_CACHE).then(function (cache) {
      return cache.match(FILE_LIST).then(function (list) {
        return list ? list.text() : null;
      });
    });
  },
  save: function (files) {
    return caches.open(SITE_CACHE).then(function (cache) {
      return Promise.all(
        files.map(function (file) {
          return saveFile(cache, file);
        }),
      ).then(function () {
        return { ok: true };
      });
    });
  },
  finish: function (text) {
    // Files of the previous list that the new one lacks are dropped. The previous list
    // says which they are: Cache.keys() over the whole site is too large for Chromium.
    var listed = {};
    JSON.parse(text).files.forEach(function (file) {
      listed[new URL(file[0], SCOPE).href] = true;
    });
    return caches.open(SITE_CACHE).then(function (cache) {
      return cache
        .match(FILE_LIST)
        .then(function (previous) {
          return previous ? previous.json() : { files: [] };
        })
        .then(function (previous) {
          return Promise.all(
            previous.files
              .map(function (file) {
                return new URL(file[0], SCOPE).href;
              })
              .filter(function (url) {
                return !listed[url];
              })
              .map(function (url) {
                return cache.delete(url);
              }),
          );
        })
        .then(function () {
          var type = { 'Content-Type': 'application/json' };
          return cache.put(FILE_LIST, new Response(text, { headers: type }));
        })
        .then(function () {
          return { ok: true };
        });
    });
  },
};

self.addEventListener('message', function (event) {
  var port = event.ports[0];
  var name = Object.keys(event.data || {}).filter(function (key) {
    return Object.prototype.hasOwnProperty.call(ACTIONS, key);
  })[0];
  if (!port || !name) return;
  event.waitUntil(
    ACTIONS[name](event.data[name]).then(
      function (answer) {
        port.postMessage(answer);
      },
      function (error) {
        port.postMessage({ ok: false, error: String(error) });
      },
    ),
  );
});

self.addEventListener('fetch', function (event) {
  var request = event.request;
  if (!handled(request)) return;
  var versioned = new URL(request.url).searchParams.has('v');
  event.respondWith(versioned ? cacheFirst(request) : networkFirst(request));
});
