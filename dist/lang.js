// Language menu at the right end of the header, after the theme toggle, as on the owner's
// profile site (nguekwang.github.io). It switches the interface text (buttons, headings,
// help) between English and Japanese. Record names, source titles and other data stay as
// the sources give them.
// - The pages are written in English. This script translates the text on the page with
//   the dictionary in i18n.js (exact strings, then patterns), and keeps translating what
//   the atlas scripts add later (a MutationObserver), so the atlas code needs no changes.
// - Without a saved choice the language follows the browser (Japanese if the browser
//   prefers Japanese, otherwise English). A pick is saved in localStorage ("lang") and
//   applies to every page. Switching adds no history entry and keeps the URL.
// - Without JavaScript the pages are in English and the menu is not shown.
// - Elements with class "notranslate" (and their children) are never translated.
(function () {
  var root = document.documentElement;
  var KEY = 'lang';
  var LANGS = [['en', 'English'], ['ja', '日本語']];
  var PROFILE = { en: 'https://nguekwang.github.io/en/?ref=langlog', ja: 'https://nguekwang.github.io/ja/?ref=langlog' };
  var ATTRS = ['placeholder', 'aria-label', 'title', 'alt'];
  var SKIP = 'script,style,code,.notranslate';

  function saved() {
    try { var v = localStorage.getItem(KEY); return v === 'en' || v === 'ja' ? v : null; }
    catch (e) { return null; }
  }
  function browser() {
    var list = navigator.languages || [navigator.language || 'en'];
    for (var i = 0; i < list.length; i++) {
      var l = String(list[i]).toLowerCase();
      if (l.indexOf('ja') === 0) return 'ja';
      if (l.indexOf('en') === 0) return 'en';
    }
    return 'en';
  }
  var lang = saved() || browser();

  // Originals of what was translated, so English can be put back without a reload.
  var textOrig = new WeakMap();
  var attrOrig = new WeakMap();
  var touched = [];

  function dict() { return (window.LANGLOG_I18N || {})[lang] || null; }
  function tr(s) {
    var d = dict();
    if (!d) return null;
    var key = s.replace(/\s+/g, ' ').trim();
    if (!key || !/[A-Za-z]/.test(key)) return null;
    var out = Object.prototype.hasOwnProperty.call(d.exact, key) ? d.exact[key] : null;
    if (out === null) {
      for (var i = 0; i < d.patterns.length; i++) {
        var m = key.match(d.patterns[i][0]);
        if (m) { out = typeof d.patterns[i][1] === 'function' ? d.patterns[i][1](m, tr) : key.replace(d.patterns[i][0], d.patterns[i][1]); break; }
      }
    }
    if (out === null) {
      // Long text: translate sentence by sentence, but only when every sentence is known.
      var parts = key.split(/(?<=\.)\s+/);
      if (parts.length > 1) {
        var done = [];
        for (var k = 0; k < parts.length; k++) {
          var p = tr(parts[k]);
          if (p === null) { done = null; break; }
          done.push(p);
        }
        if (done) out = done.join(d.join != null ? d.join : ' ');
      }
    }
    if (out === null || out === key) return null;
    var lead = s.match(/^\s*/)[0], tail = s.match(/\s*$/)[0];
    return lead + out + tail;
  }
  function skip(el) { return !el || (el.closest && el.closest(SKIP)); }
  function doText(n) {
    if (skip(n.parentElement)) return;
    var t = tr(n.nodeValue);
    if (t === null) return;
    if (!textOrig.has(n)) touched.push(n);
    textOrig.set(n, n.nodeValue);
    n.nodeValue = t;
  }
  function doAttrs(el) {
    if (skip(el)) return;
    for (var i = 0; i < ATTRS.length; i++) {
      var a = ATTRS[i];
      if (!el.hasAttribute(a)) continue;
      var t = tr(el.getAttribute(a));
      if (t === null) continue;
      var o = attrOrig.get(el);
      if (!o) { o = {}; attrOrig.set(el, o); touched.push(el); }
      o[a] = el.getAttribute(a);
      el.setAttribute(a, t);
    }
  }
  function walk(node) {
    if (node.nodeType === 3) { doText(node); return; }
    if (node.nodeType !== 1 || skip(node)) return;
    doAttrs(node);
    var w = document.createTreeWalker(node, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
    var n;
    while ((n = w.nextNode())) {
      if (n.nodeType === 3) doText(n); else doAttrs(n);
    }
  }

  var observer = null;
  function observe() {
    if (observer || !window.MutationObserver) return;
    observer = new MutationObserver(function (records) {
      observer.disconnect();
      for (var i = 0; i < records.length; i++) {
        var r = records[i];
        if (r.type === 'characterData') doText(r.target);
        else if (r.type === 'attributes') doAttrs(r.target);
        else for (var j = 0; j < r.addedNodes.length; j++) walk(r.addedNodes[j]);
      }
      observer.observe(document.documentElement, OPTS);
    });
    observer.observe(document.documentElement, OPTS);
  }
  var OPTS = { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ATTRS };

  function restore() {
    if (observer) { observer.disconnect(); observer = null; }
    for (var i = 0; i < touched.length; i++) {
      var n = touched[i];
      if (n.nodeType === 3) { if (textOrig.has(n)) n.nodeValue = textOrig.get(n); textOrig.delete(n); }
      else {
        var o = attrOrig.get(n);
        if (o) for (var a in o) n.setAttribute(a, o[a]);
        attrOrig.delete(n);
      }
    }
    touched = [];
  }

  function profileLinks() {
    Array.prototype.forEach.call(document.querySelectorAll('a[href^="https://nguekwang.github.io/"]'), function (a) {
      a.href = PROFILE[lang] || PROFILE.en;
    });
  }

  function menu() {
    var box = document.querySelector('body > header .tools');
    if (!box) return;
    var d = box.querySelector('.langmenu');
    if (!d) {
      d = document.createElement('details');
      d.className = 'langmenu notranslate';
      box.appendChild(d);
      d.addEventListener('click', function (e) {
        var b = e.target.closest('button[data-lang]');
        if (!b) return;
        d.open = false;
        set(b.getAttribute('data-lang'), true);
      });
      document.addEventListener('click', function (e) { if (d.open && !d.contains(e.target)) d.open = false; });
      document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && d.open) { d.open = false; d.querySelector('summary').focus(); } });
    }
    var name = LANGS.filter(function (l) { return l[0] === lang; })[0][1];
    var items = LANGS.map(function (l) {
      return l[0] === lang
        ? '<li><span lang="' + l[0] + '" aria-current="true">' + l[1] + '</span></li>'
        : '<li><button type="button" lang="' + l[0] + '" data-lang="' + l[0] + '">' + l[1] + '</button></li>';
    }).join('');
    d.innerHTML = '<summary aria-label="Language: ' + name + '"><span class="full">' + name + '</span><span class="short" aria-hidden="true">' + lang.toUpperCase() + '</span></summary><div class="panel"><ul>' + items + '</ul></div>';
  }

  function apply() {
    root.setAttribute('lang', lang);
    restore();
    if (lang !== 'en') { walk(document.documentElement); observe(); }
    profileLinks();
    menu();
  }

  function set(l, save) {
    if (l === lang) return;
    lang = l;
    if (save) { try { localStorage.setItem(KEY, l); } catch (e) { /* private mode: this page only */ } }
    apply();
    document.dispatchEvent(new Event('langchange'));
  }

  root.setAttribute('lang', lang);
  if (lang !== 'en') {
    // Translate the head now (title) and the body as the parser builds it, so English
    // does not flash before the translation.
    walk(document.documentElement);
    observe();
  }
  document.addEventListener('DOMContentLoaded', function () {
    if (lang !== 'en') walk(document.body);
    profileLinks();
    menu();
    document.dispatchEvent(new Event('langchange'));
  });
  window.LANGLOG_LANG = function () { return lang; };
})();
