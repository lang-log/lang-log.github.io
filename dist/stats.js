// Motion on the Stats page (dist/stats/, written by tools/build_home.py): each bar grows
// from zero and each marked number (class "count") counts up from 0 when it scrolls into
// view. Both last --stats-duration, set once in dist/style.css (owner, 2026-11-07: one
// value for the bars and the count, 1.6 s); this script reads it, so change it there only.
// - The page is built with the final numbers and full bars, so without JavaScript, without
//   IntersectionObserver or with "reduce motion" turned on, nothing moves and nothing is
//   hidden. The script only starts the motion; the CSS that hides the bars before it runs
//   applies only under html.stats-motion, which this script sets.
// - Loaded in <head> so the class is set before the first paint (no flash of full bars).
// - Numbers are written in the build's English form ("30,885") as text-node values, so
//   lang.js translates each step as it does any number it sees.
// - While lang.js hides the page to load a dictionary (html.i18n-wait), the motion waits.
(function () {
  var root = document.documentElement;
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce || !window.IntersectionObserver || !window.requestAnimationFrame) return;
  root.classList.add('stats-motion');

  function format(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ','); }
  function textNode(el) {
    for (var c = el.firstChild; c; c = c.nextSibling) if (c.nodeType === 3) return c;
    return null;
  }

  // --stats-duration from the stylesheet ("1.6s" or "1600ms") in ms; 0 if unreadable,
  // which shows the final number at once.
  function duration() {
    var v = window.getComputedStyle(root).getPropertyValue('--stats-duration').trim();
    var n = parseFloat(v);
    if (!(n >= 0)) return 0;
    return /ms$/.test(v) ? n : n * 1000;
  }

  // Count one element up to the number it was built with.
  function count(el) {
    var node = textNode(el);
    var target = el.getAttribute('data-value');
    if (!node || target === null) return;
    var end = Number(target);
    var ms = duration();
    var start = null;
    function step(now) {
      if (start === null) start = now;
      var t = ms > 0 ? Math.min((now - start) / ms, 1) : 1;
      var eased = 1 - Math.pow(1 - t, 3);
      node.nodeValue = format(t < 1 ? Math.round(end * eased) : end);
      if (t < 1) window.requestAnimationFrame(step);
    }
    window.requestAnimationFrame(step);
  }

  function run() {
    var counts = document.querySelectorAll('.count[data-value]');
    for (var i = 0; i < counts.length; i++) {
      var n = textNode(counts[i]);
      if (n) n.nodeValue = '0';
    }
    var io = new IntersectionObserver(function (entries) {
      for (var j = 0; j < entries.length; j++) {
        var e = entries[j];
        if (!e.isIntersecting) continue;
        io.unobserve(e.target);
        e.target.classList.add('in');
        // A hero figure holds its number; a bar's number is the next item in its row.
        var num = e.target.matches('.bar') ? e.target.nextElementSibling : e.target.querySelector('.count');
        if (num && num.matches('.count')) count(num);
      }
    });
    // The .bars rows are display: contents (no box to observe), so the bar itself is watched.
    var watched = document.querySelectorAll('.stat-hero > div, .bars .bar');
    for (var g = 0; g < watched.length; g++) io.observe(watched[g]);
  }

  function whenShown() {
    if (!root.classList.contains('i18n-wait')) { run(); return; }
    var mo = new MutationObserver(function () {
      if (root.classList.contains('i18n-wait')) return;
      mo.disconnect();
      run();
    });
    mo.observe(root, { attributes: true, attributeFilter: ['class'] });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', whenShown);
  else whenShown();
})();
