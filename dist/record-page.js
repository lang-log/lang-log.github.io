'use strict';
// Parts of a record page that need JavaScript (the page is complete without them):
// - the Hugging Face models section, filled from the Hub when it scrolls into view;
// - the Tree section, whose button asks dist/tree.js to draw the branch.
(() => {
  const section = document.getElementById('tree-section'),
    button = document.getElementById('show-tree');
  if (section && button && window.LangLogTree) {
    section.hidden = false;
    const start = () => {
      button.parentElement.hidden = true;
      window.LangLogTree.start();
    };
    button.addEventListener('click', start);
    // A shared link to a drawn tree (?view=tree or other tree state) opens with the tree.
    if (['view', 'dialects', 'x'].some((k) => new URLSearchParams(location.search).has(k))) start();
  }
  const hf = document.getElementById('hf-models');
  if (hf && window.LanguageModels) {
    const node = { name: hf.dataset.name, level: hf.dataset.level, iso: hf.dataset.iso };
    const task = new URLSearchParams(location.search).get('task') || '';
    const mount = () => {
      hf.hidden = false;
      window.LanguageModels.mount(hf, node, {
        task,
        onTask: (t) => {
          const u = new URL(location.href);
          if (t) u.searchParams.set('task', t);
          else u.searchParams.delete('task');
          try {
            history.replaceState(null, '', u);
          } catch {
            /* the browser refused (rate limit): keep the old URL */
          }
        },
      });
    };
    // A hidden element never intersects, so watch the section's place in the page (its previous sibling).
    const spot = hf.previousElementSibling || hf.parentElement;
    if ('IntersectionObserver' in window) {
      const io = new IntersectionObserver(
        (es) => {
          if (es.some((e) => e.isIntersecting)) {
            io.disconnect();
            mount();
          }
        },
        { rootMargin: '300px' },
      );
      io.observe(spot);
    } else mount();
  }
})();
