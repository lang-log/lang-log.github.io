// Registers the service worker, dist/sw.js, which keeps the pages and files a visitor has
// opened so they open again offline (.claude/rules/pwa.md). Loaded in <head> by every page
// (tools/pwa.py writes the tag).
// The worker's address comes from this script's own address, so it is the sw.js at the root
// of the site the page belongs to: the live site, or a pull request preview under
// /preview/pr-<number>/. Its scope is that folder.
// It also gives window.LangLogOffline, which the "save the whole site" button below uses:
// - status() resolves to true when the whole site is stored.
// - size() resolves to the size in bytes of every file in offline-files.json (tools/pwa.py).
// - save(progress) stores every file in that list, BATCH_FILES at a
//   time, and calls progress(filesDone, filesTotal) after each batch. Files with the same
//   hash as in the last finished save are skipped, and the worker skips any it holds with
//   the same hash, so after a failure or a new release a second call fetches only what is
//   missing or changed.
// - Once the whole site is stored, every page opened online checks offline-version.txt (a
//   few bytes) and, when the list changed after a release, runs save() in the background, so
//   only the changed files are fetched (the owner's decision, 2026-11-23).
(function () {
  if (!('serviceWorker' in navigator) || !document.currentScript) return;
  var worker = new URL('sw.js', document.currentScript.src).href;
  var fileList = new URL('offline-files.json', document.currentScript.src).href;
  var listVersion = new URL('offline-version.txt', document.currentScript.src).href;
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

  function fetchText(url) {
    return fetch(url, { cache: 'no-cache' }).then(function (response) {
      if (!response.ok) throw new Error(url + ': HTTP ' + response.status);
      return response.text();
    });
  }

  // The text of offline-files.json, fetched once per page: size() and save() both read it.
  var listText = null;
  function list() {
    if (!listText) listText = fetchText(fileList);
    listText.catch(function () {
      listText = null; // a failed fetch is tried again on the next call
    });
    return listText;
  }

  function size() {
    return list().then(function (text) {
      return JSON.parse(text).files.reduce(function (sum, file) {
        return sum + file[1];
      }, 0);
    });
  }

  // One save at a time across the visitor's tabs (Web Locks), so the button and a
  // background update never fetch the same files twice. Without Web Locks, run at once.
  function oneAtATime(run) {
    if (!navigator.locks) return run();
    return navigator.locks.request('lang-log-save', run);
  }

  function save(progress) {
    return oneAtATime(function () {
      return saveNow(progress);
    });
  }

  function saveNow(progress) {
    // Ask the browser to keep the copy instead of clearing it when space runs low.
    if (navigator.storage && navigator.storage.persist) navigator.storage.persist();
    return Promise.all([list(), fetchText(listVersion), ask({ previous: true })]).then(
      function (texts) {
        var text = texts[0];
        var version = texts[1].trim();
        var files = JSON.parse(text).files;
        // Files whose hash is the same as in the last finished save are already stored.
        var had = {};
        if (texts[2]) {
          JSON.parse(texts[2]).files.forEach(function (file) {
            had[file[0]] = file[2];
          });
        }
        var total = files.length;
        files = files.filter(function (file) {
          return had[file[0]] !== file[2];
        });
        var done = total - files.length;
        function next(start) {
          if (start >= files.length) return ask({ finish: { list: text, version: version } });
          var batch = files.slice(start, start + BATCH_FILES);
          return ask({ save: batch }).then(function () {
            done += batch.length;
            progress(done, total);
            return next(start + BATCH_FILES);
          });
        }
        progress(done, total);
        return next(0);
      },
    );
  }

  window.LangLogOffline = {
    status: function () {
      return ask({ status: true }).then(function (answer) {
        return answer.saved;
      });
    },
    size: size,
    save: save,
  };

  // The "save the whole site" button (owner, 2026-11-23), at the end of the page's footer, or
  // in a footer of its own on pages without one. Its words are English; dist/lang.js
  // translates them like the rest of the page, and LANGLOG_TEXT the confirm() question.
  var BYTES_PER_MB = 1000 * 1000;
  function text(english) {
    return window.LANGLOG_TEXT ? window.LANGLOG_TEXT(english) : english;
  }
  function addButton() {
    var footers = document.querySelectorAll('body > footer');
    var footer = footers[footers.length - 1];
    if (!footer) {
      footer = document.createElement('footer');
      document.body.appendChild(footer);
    }
    var box = document.createElement('span');
    box.className = 'offline-save';
    var button = document.createElement('button');
    button.type = 'button';
    button.textContent = 'Save the whole site for offline use';
    var status = document.createElement('span');
    status.setAttribute('role', 'status');
    box.appendChild(button);
    box.appendChild(status);
    footer.appendChild(box);

    function failed() {
      status.textContent = 'Could not save. Please try again.';
      button.disabled = false;
    }
    button.addEventListener('click', function () {
      button.disabled = true;
      size()
        .then(function (bytes) {
          var mb = Math.round(bytes / BYTES_PER_MB).toLocaleString('en-US');
          var question =
            'This saves the whole site (about ' + mb + ' MB) on this device. Continue?';
          if (!window.confirm(text(question))) {
            button.disabled = false;
            return;
          }
          return save(function (done, total) {
            status.textContent =
              'Saving… ' +
              done.toLocaleString('en-US') +
              ' / ' +
              total.toLocaleString('en-US') +
              ' files';
          }).then(function () {
            status.textContent = 'Saved. The site now opens offline.';
            button.disabled = false;
          });
        })
        .catch(failed);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', addButton);
  else addButton();

  // After a release, brings a stored copy of the whole site up to date in the background.
  // Nothing happens unless the visitor stored the whole site before. A failure is left for
  // the next page to try again.
  function update() {
    if (navigator.onLine === false) return;
    window.LangLogOffline.status()
      .then(function (saved) {
        if (!saved) return;
        return Promise.all([fetchText(listVersion), ask({ version: true })]).then(
          function (versions) {
            if (versions[0].trim() !== versions[1]) return save(function () {});
          },
        );
      })
      .catch(function () {});
  }

  window.addEventListener('load', function () {
    // updateViaCache "none": always ask the server for a new sw.js, past the ten-minute
    // browser cache of GitHub Pages, so a deployed change reaches visitors on their next visit.
    navigator.serviceWorker
      .register(worker, { updateViaCache: 'none' })
      .then(update)
      .catch(function () {
        // Some browsers refuse service workers (private windows, blocked storage). The site
        // works the same without one; only the offline copies are missing.
      });
  });
})();
