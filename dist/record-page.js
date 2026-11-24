'use strict';
// Parts of a record page that need JavaScript (the page is complete without them):
// - the Hugging Face models section, filled from the Hub when it scrolls into view;
// - the Tree section, whose button asks dist/tree.js to draw the branch;
// - country and script names and percentages, which the browser writes in the page's
//   language (Intl), so no dictionary.
(() => {
  // Codes the browser names (Intl.DisplayNames) and numbers it writes (Intl.NumberFormat) in
  // the page's language: countries (data-region), scripts (data-script), shares (data-percent)
  // and counts (data-number).
  const named = [
    ['region', document.querySelectorAll('[data-region]')],
    ['script', document.querySelectorAll('[data-script]')],
  ];
  const percents = document.querySelectorAll('[data-percent]');
  const numbers = document.querySelectorAll('[data-number]');
  const locale = () =>
    window.LANGLOG_LOCALE ? window.LANGLOG_LOCALE() : document.documentElement.lang || 'en';
  const localize = () => {
    for (const [type, els] of named) {
      let names;
      try {
        names = new Intl.DisplayNames([locale()], { type });
      } catch {
        continue; // the codes stay as they are
      }
      for (const el of els) {
        const code = el.dataset[type];
        try {
          el.textContent = names.of(code) || code;
        } catch {
          el.textContent = code;
        }
      }
    }
    let share, count;
    try {
      share = new Intl.NumberFormat(locale(), { style: 'percent', maximumFractionDigits: 2 });
      count = new Intl.NumberFormat(locale());
    } catch {
      return; // the numbers stay as written
    }
    for (const el of percents) el.textContent = share.format(Number(el.dataset.percent) / 100);
    for (const el of numbers) el.textContent = count.format(Number(el.dataset.number));
  };
  if (named.some(([, els]) => els.length) || percents.length || numbers.length) {
    localize();
    // dist/lang.js sets <html lang> when the visitor changes the language.
    new MutationObserver(localize).observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['lang'],
    });
  }
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
    if (['view', 'x'].some((k) => new URLSearchParams(location.search).has(k))) start();
  }
  const hf = document.getElementById('hf-models');
  if (hf && window.LanguageModels) {
    const node = { name: hf.dataset.name, level: hf.dataset.level, iso: hf.dataset.iso };
    const task = new URLSearchParams(location.search).get('task') || '';
    // Its group starts hidden when the models are all it holds (tools/build_paths.py).
    const groupOf = hf.closest('.record-group');
    if (groupOf) groupOf.hidden = false;
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
