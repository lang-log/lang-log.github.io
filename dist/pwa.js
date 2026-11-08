// Registers the service worker, dist/sw.js, which keeps the pages and files a visitor has
// opened so they open again offline (.claude/rules/pwa.md). Loaded in <head> by every page
// (tools/pwa.py writes the tag).
// The worker's address comes from this script's own address, so it is the sw.js at the root
// of the site the page belongs to: the live site, or a pull request preview under
// /preview/pr-<number>/. Its scope is that folder.
(function () {
  if (!('serviceWorker' in navigator) || !document.currentScript) return;
  var worker = new URL('sw.js', document.currentScript.src).href;
  window.addEventListener('load', function () {
    // updateViaCache "none": always ask the server for a new sw.js, past the ten-minute
    // browser cache of GitHub Pages, so a deployed change reaches visitors on their next visit.
    navigator.serviceWorker.register(worker, { updateViaCache: 'none' }).catch(function () {
      // Some browsers refuse service workers (private windows, blocked storage). The site
      // works the same without one; only the offline copies are missing.
    });
  });
})();
