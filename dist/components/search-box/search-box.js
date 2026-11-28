'use strict';
// The search box is a plain GET form to the results page, dist/q.html at <site>/q?q=<terms>
// (dist/components/search-results/search-results.js), so it works without this script; this keeps an empty box from leaving
// the page. Top-page addresses with ?q=<terms> are sent there by dist/search-redirect.js.
(() => {
  const form = document.querySelector('form.home-search');
  if (!form) return;
  form.addEventListener('submit', (e) => {
    if (form.elements.q.value.trim()) return;
    e.preventDefault();
    form.elements.q.focus();
  });
})();
