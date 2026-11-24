// Sends a top-page address with ?q=<terms> (old links, and search shortcuts set up in a
// browser by hand) to the search results page, before anything is drawn. It is loaded in
// <head>, before the stylesheets, so the top page never shows first. The results page's
// address comes from the data-results attribute of this script's own <script> element
// (written by tools/build_home.py, the same value as the search form's action), so the
// address stays relative and works on any host and in previews.
(() => {
  const terms = new URLSearchParams(location.search).get('q');
  if (terms === null || !terms.trim()) return;
  const results = document.currentScript.dataset.results;
  if (!results) return;
  location.replace(results + location.search + location.hash);
})();
