'use strict';
// Decides, in the <head> of dist/404.html, whether this address is the search results
// page <site>/q=<terms> (owner, 2026-11-07; dist/search.js draws the results).
//
// It runs before the body is drawn, so the page is the search page from its first paint:
// <html> gets the class "search-route", and style.css hides the not-found message and
// shows the search page from that class. Deciding this at the end of the body instead
// (as search.js did) let the browser paint "Page not found" while the scripts at the end
// of the body were still loading, which looked like an empty search on slow connections.
//
// search.js reads the address through window.SearchRoute, so the pattern lives only here.
window.SearchRoute = (() => {
  const PATTERN = /^(.*\/)q=([^/]*)$/;
  // Keep the title suffix 404.html was written with (tools/site_brand.py).
  const titleSuffix = document.title.slice(document.title.lastIndexOf(' · '));
  const api = {
    // [site root, raw terms], or null when this is not a search address. The site root is
    // '/' on the live site and '/preview/pr-<n>/' in a pull request preview.
    match() {
      const m = location.pathname.match(PATTERN);
      return m && [m[1], m[2]];
    },
    terms(raw) {
      try {
        return decodeURIComponent(raw.replace(/\+/g, ' ')).trim();
      } catch {
        return raw.trim();
      }
    },
    setTitle(q) {
      document.title = (q ? q + ' · ' : '') + 'Search results' + titleSuffix;
    },
  };
  const m = api.match();
  if (m) {
    const q = api.terms(m[1]);
    document.documentElement.classList.add('search-route');
    api.setTitle(q);
    // Put the terms in the search box as soon as the parser adds it, so the box is never
    // drawn empty while the scripts at the end of the body load. search.js keeps it after.
    const fill = () => {
      const input = document.getElementById('search-q');
      if (!input) return false;
      input.value = q;
      return true;
    };
    const watch = new MutationObserver(() => {
      if (fill()) watch.disconnect();
    });
    watch.observe(document.documentElement, { childList: true, subtree: true });
  }
  return api;
})();
