// Registers the service worker, dist/sw.js, which keeps the pages and files a visitor has
// opened so they open again offline (.claude/rules/pwa.md). Loaded in <head> by every page
// (tools/pwa.py writes the tag).
// The worker's address comes from this script's own address, so it is the sw.js at the root
// of the site the page belongs to: the live site, or a pull request preview under
// /preview/pr-<number>/. Its scope is that folder.
// It also gives window.LangLogOffline, which the "save the whole site" button uses:
// - status() resolves to true when the whole site is stored.
// - save(progress) stores every file in offline-files.json (tools/pwa.py), BATCH_FILES at a
//   time, and calls progress(bytesDone, bytesTotal) after each batch. Files with the same
//   hash as in the last finished save are skipped, and the worker skips any it holds with
//   the same hash, so after a failure or a new release a second call fetches only what is
//   missing or changed.
(function () {
  if (!('serviceWorker' in navigator) || !document.currentScript) return;
  var worker = new URL('sw.js', document.currentScript.src).href;
  var fileList = new URL('offline-files.json', document.currentScript.src).href;
  // Files fetched at once: a few in parallel keeps the download fast without many
  // requests waiting on the server at the same time.
  var BATCH_FILES = 8;

  // Sends one message to the worker and resolves to its answer (dist/sw.js, ACTIONS).
  function ask(message) {
    return navigator.serviceWorker.ready.then(function (registration) {
      return new Promise(function (resolve, reject) {
        var channel = new MessageChannel();
        channel.port1.onmessage = function (event) {
          if (event.data && event.data.ok === false) reject(new Error(event.data.error));
          else resolve(event.data);
        };
        registration.active.postMessage(message, [channel.port2]);
      });
    });
  }

  function save(progress) {
    // Ask the browser to keep the copy instead of clearing it when space runs low.
    if (navigator.storage && navigator.storage.persist) navigator.storage.persist();
    return fetch(fileList, { cache: 'no-cache' })
      .then(function (response) {
        if (!response.ok) throw new Error(fileList + ': HTTP ' + response.status);
        return response.text();
      })
      .then(function (text) {
        return ask({ previous: true }).then(function (previous) {
          return [text, previous];
        });
      })
      .then(function (texts) {
        var text = texts[0];
        var files = JSON.parse(text).files;
        // Files whose hash is the same as in the last finished save are already stored.
        var had = {};
        if (texts[1]) {
          JSON.parse(texts[1]).files.forEach(function (file) {
            had[file[0]] = file[2];
          });
        }
        var total = 0;
        var done = 0;
        files = files.filter(function (file) {
          total += file[1];
          if (had[file[0]] !== file[2]) return true;
          done += file[1];
          return false;
        });
        function next(start) {
          if (start >= files.length) return ask({ finish: text });
          var batch = files.slice(start, start + BATCH_FILES);
          return ask({ save: batch }).then(function () {
            batch.forEach(function (file) {
              done += file[1];
            });
            progress(done, total);
            return next(start + BATCH_FILES);
          });
        }
        progress(done, total);
        return next(0);
      });
  }

  window.LangLogOffline = {
    status: function () {
      return ask({ status: true }).then(function (answer) {
        return answer.saved;
      });
    },
    save: save,
  };

  window.addEventListener('load', function () {
    // updateViaCache "none": always ask the server for a new sw.js, past the ten-minute
    // browser cache of GitHub Pages, so a deployed change reaches visitors on their next visit.
    navigator.serviceWorker.register(worker, { updateViaCache: 'none' }).catch(function () {
      // Some browsers refuse service workers (private windows, blocked storage). The site
      // works the same without one; only the offline copies are missing.
    });
  });
})();
