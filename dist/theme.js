// Light/dark theme toggle, the round button at the right end of the header. It works like
// the one on the owner's profile site (nguekwang.github.io):
// - Without a saved choice the page follows the system setting (prefers-color-scheme).
// - A click saves the other theme in localStorage and sets <html data-theme="light|dark">,
//   which the colour tokens at the top of style.css read. The choice is per site, so it
//   stays on every page.
// - This file is loaded in <head>, before the page is drawn, so a saved theme is applied
//   without a flash of the other one.
// - The button is added by this script, because it does nothing without JavaScript; without
//   JavaScript the page follows the system setting.
// - A "themechange" event on document tells the canvas tree (tree.js) to redraw.
(function () {
  var root = document.documentElement;
  var KEY = 'theme';
  var media = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
  var LABEL = { en: 'Dark theme', ja: 'ダークテーマ' };

  function saved() {
    try { var v = localStorage.getItem(KEY); return v === 'light' || v === 'dark' ? v : null; }
    catch (e) { return null; }
  }
  function current() {
    return root.getAttribute('data-theme') || (media && media.matches ? 'dark' : 'light');
  }
  function sync() {
    var dark = current() === 'dark';
    Array.prototype.forEach.call(document.querySelectorAll('.theme-toggle'), function (b) {
      b.setAttribute('aria-pressed', dark ? 'true' : 'false');
      var label = LABEL[(root.getAttribute('lang') || 'en').split('-')[0]] || LABEL.en;
      b.setAttribute('aria-label', label);
      b.title = label;
    });
  }
  function changed() {
    sync();
    document.dispatchEvent(new Event('themechange'));
  }

  var s = saved();
  if (s) root.setAttribute('data-theme', s);

  var BUTTON = '<svg class="moon" viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false"><path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z"/></svg>' +
    '<svg class="sun" viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="4.5"/><path d="M12 1.5v3M12 19.5v3M1.5 12h3M19.5 12h3M4.6 4.6l2.1 2.1M17.3 17.3l2.1 2.1M4.6 19.4l2.1-2.1M17.3 6.7l2.1-2.1"/></svg>';

  // The header keeps the brand on the left and one element on the right. The controls go
  // into a .tools group after that element (see header-tools in style.css).
  function tools() {
    var header = document.querySelector('body > header');
    if (!header) return null;
    var box = header.querySelector('.tools');
    if (box) return box;
    box = document.createElement('div');
    box.className = 'tools';
    var last = header.lastElementChild;
    if (last && !last.classList.contains('brand')) box.appendChild(last);
    header.appendChild(box);
    return box;
  }

  document.addEventListener('DOMContentLoaded', function () {
    var box = tools();
    if (box && !box.querySelector('.theme-toggle')) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'theme-toggle';
      b.innerHTML = BUTTON;
      box.appendChild(b);
    }
    sync();
  });

  document.addEventListener('click', function (e) {
    var b = e.target.closest ? e.target.closest('.theme-toggle') : null;
    if (!b) return;
    var next = current() === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem(KEY, next); } catch (e2) { /* private mode: keep for this page only */ }
    changed();
  });

  document.addEventListener('langchange', sync);
  if (media) {
    if (media.addEventListener) media.addEventListener('change', changed);
    else if (media.addListener) media.addListener(changed);
  }
})();
