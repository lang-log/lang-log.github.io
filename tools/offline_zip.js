// Writes the whole site as Markdown and PDF files in one interface language, for the ZIP files
// attached to each GitHub Release (.claude/rules/releases.md; the owner's decision, 2026-11-24,
// replacing the "save the whole site" button):
//   build/offline/lang-log.<code>/records/<record path>/index.md   one file per record, in the tree's folders
//   build/offline/lang-log.<code>/pdf/<top-level folder>.pdf        one PDF per top-level family
// Run after tools/build_site.sh, from the repository root, with Playwright's Chromium:
//   node tools/offline_zip.js <code> [<top-level folder> ...]
// Naming top-level folders builds only those (for a quick look); the release builds them all.
//
// The files are read from the built record pages themselves, in a browser, so they hold exactly
// what a visitor sees: dist/lang.js translates each page as it does for visitors, and this
// script only turns the page's main content and its source credit into Markdown (and the same
// part, as HTML, into the PDF). Parts that need a script or the network to mean anything (the
// map, the tree, the view switch and conditions, the Hugging Face models) are left out.
/* global document, window, Node -- readPage() runs in the page, not in Node.js */
const fs = require('fs'),
  { execFileSync } = require('child_process'),
  path = require('path'),
  { chromium } = require('playwright'),
  { DIST, serve } = require('./serve_dist');

const ROOT = path.join(__dirname, '..');
const OUT = path.join(ROOT, 'build', 'offline');
// Pages open at the same time; each takes about 0.1 s, so 8 keep a GitHub runner busy without
// running out of memory.
const PARALLEL = 8;
// Every record page (tools/build_paths.py) loads record-page.js; no other page does.
const RECORD_MARK = 'record-page.js"></script>';
// Links inside the site come back from the page as LINK + path, and are pointed at the right
// file (or the live site) here, where the list of records is.
const LINK = 'lang-log-path:';
// Stylesheets the PDF is printed with: the site's own, so it looks like the pages.
const PDF_STYLES = ['style.css', 'record.css'];
// Paper and margins of the PDF.
const PDF_OPTIONS = {
  format: 'A4',
  margin: { top: '15mm', bottom: '15mm', left: '12mm', right: '12mm' },
};

// A constant written in another file of the repository, read rather than copied.
function constant(file, pattern) {
  const m = fs.readFileSync(path.join(ROOT, file), 'utf8').match(pattern);
  if (!m) throw new Error(`${pattern} not found in ${file}`);
  return m[1];
}
// The interface languages (LANGS in dist/lang.js, read by tools/build_i18n.py) and the live
// site (SITE_URL in tools/site_brand.py).
const LANGUAGES = JSON.parse(
  execFileSync('python3', [path.join(ROOT, 'tools', 'build_i18n.py'), '--languages'], {
    encoding: 'utf8',
  }),
);
const SITE_URL = constant('tools/site_brand.py', /^SITE_URL = "([^"]+)"/m);

// The path of every record page, such as "japonic/" or "japonic/japanese/", sorted so that a
// family comes before its members.
function recordPaths(only) {
  const found = [];
  const walk = (dir, rel) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue;
      const sub = path.join(dir, entry.name),
        subRel = rel + entry.name + '/',
        page = path.join(sub, 'index.html');
      if (fs.existsSync(page) && fs.readFileSync(page, 'utf8').includes(RECORD_MARK))
        found.push(subRel);
      walk(sub, subRel);
    }
  };
  walk(DIST, '');
  return found.filter((p) => !only.length || only.includes(p.split('/')[0])).sort();
}

// In the page: the main content and the source credit, as Markdown and as plain HTML.
function readPage(link) {
  const SKIP =
    'script,style,svg,figure,[hidden],.hf-models,#tree-section,.record-views,.explorer,' +
    'details.menu,.toolbar,.data-label,button';
  const origin = window.location.origin;
  const target = (a) => {
    const url = new URL(a.getAttribute('href'), window.location.href);
    return url.origin === origin
      ? link + url.pathname.replace(/^\//, '') + url.search + url.hash
      : url.href;
  };
  const clean = (t) => t.replace(/\s+/g, ' ');

  function inline(node) {
    let out = '';
    for (const c of node.childNodes) {
      if (c.nodeType === Node.TEXT_NODE) out += clean(c.textContent);
      else if (c.nodeType !== Node.ELEMENT_NODE || c.matches(SKIP)) continue;
      else if (c.tagName === 'A' && c.getAttribute('href')) {
        const text = inline(c).trim().replace(/[[\]]/g, '\\$&');
        out += text ? '[' + text + '](' + target(c) + ')' : '';
      } else if (c.tagName === 'BR') out += ' ';
      // Blocks inside a table cell (a list of names after its count) stay apart by a space.
      else if (/^(SUMMARY|LI|P|DIV|UL|OL)$/.test(c.tagName)) out += ' ' + inline(c) + ' ';
      else if (c.tagName === 'STRONG' || c.tagName === 'B') out += '**' + inline(c).trim() + '**';
      else if (c.tagName === 'EM' || c.tagName === 'I') out += '*' + inline(c).trim() + '*';
      else out += inline(c);
    }
    return out;
  }

  function table(t) {
    const rows = [...t.querySelectorAll('tr')].map((tr) =>
      [...tr.children]
        .filter((c) => !c.matches(SKIP))
        .map((c) => clean(inline(c)).replace(/\|/g, '\\|').trim()),
    );
    if (!rows.length) return '';
    const width = Math.max(...rows.map((r) => r.length));
    const head = t.querySelector('thead tr') ? rows.shift() : Array(width).fill('');
    const line = (r) => '| ' + [...r, ...Array(width - r.length).fill('')].join(' | ') + ' |';
    return [line(head), line(Array(width).fill('---')), ...rows.map(line)].join('\n');
  }

  function blocks(node) {
    const out = [];
    for (const c of node.children) {
      if (c.matches(SKIP)) continue;
      const tag = c.tagName;
      if (/^H[1-6]$/.test(tag)) out.push('#'.repeat(Number(tag[1])) + ' ' + inline(c).trim());
      else if (tag === 'TABLE') out.push(table(c));
      else if (tag === 'UL' || tag === 'OL')
        out.push(
          [...c.children]
            .filter((li) => !li.matches(SKIP))
            .map((li, i) => (tag === 'OL' ? i + 1 + '. ' : '- ') + inline(li).trim())
            .join('\n'),
        );
      else if (tag === 'P' || tag === 'NAV' || tag === 'SUMMARY') out.push(inline(c).trim());
      else out.push(...blocks(c));
    }
    return out.filter((b) => b);
  }

  const parts = [document.querySelector('main'), document.querySelector('footer.credit')].filter(
    (e) => e,
  );
  const html = parts
    .map((e) => {
      const copy = e.cloneNode(true);
      // Links first, while each copy still lines up with its original.
      const originals = [...e.querySelectorAll('a[href]')];
      [...copy.querySelectorAll('a[href]')].forEach((a, i) => {
        a.setAttribute('href', target(originals[i]));
        a.removeAttribute('target');
      });
      copy.querySelectorAll(SKIP).forEach((s) => s.remove());
      return copy.outerHTML;
    })
    .join('');
  return {
    markdown: parts.flatMap(blocks).join('\n\n') + '\n',
    html,
    lang: document.documentElement.lang,
    dir: document.documentElement.dir || 'ltr',
  };
}

// Points LINK + path at another record's file (or its place in the PDF), or at the live site.
function resolveLinks(text, here, records, inPdf) {
  return text.replace(new RegExp(LINK + '([^)"\\s]*)', 'g'), (_, rest) => {
    const p = rest.replace(/[?#].*$/, ''),
      hash = rest.slice(p.length).replace(/^\?[^#]*/, '');
    if (!records.has(p)) return SITE_URL + rest;
    if (inPdf) return '#' + encodeURIComponent(p);
    return '../'.repeat(here.split('/').length - 1) + p + 'index.md' + hash;
  });
}

const escapeHtml = (t) => t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');

async function main() {
  const [code, ...only] = process.argv.slice(2);
  if (!LANGUAGES.includes(code)) {
    console.error('usage: node tools/offline_zip.js <code> [<top-level folder> ...]');
    console.error('codes: ' + LANGUAGES.join(' '));
    process.exit(2);
  }
  const paths = recordPaths(only);
  const records = new Set(paths);
  const out = path.join(OUT, 'lang-log.' + code);
  fs.rmSync(out, { recursive: true, force: true });

  const server = await serve();
  const origin = 'http://127.0.0.1:' + server.address().port;
  const browser = await chromium.launch();
  const context = await browser.newContext({ serviceWorkers: 'block' });
  await context.addInitScript((lang) => {
    try {
      window.localStorage.setItem('lang', lang);
    } catch {
      // Without storage the page stays in English; the wait below then fails.
    }
  }, code);
  // Only the site itself: nothing that is left out of the files needs to load.
  await context.route(
    (url) => !url.href.startsWith(origin),
    (route) => route.abort(),
  );

  const families = new Map(); // top-level folder -> [{ path, html }], in tree order
  let next = 0;
  let pageLang = code,
    pageDir = 'ltr';
  const started = Date.now();
  async function worker() {
    const page = await context.newPage();
    while (next < paths.length) {
      const here = paths[next++];
      await page.goto(origin + '/' + here, { waitUntil: 'load' });
      // dist/lang.js keeps the page hidden (class i18n-wait) until the dictionary is in.
      await page.waitForFunction(
        (lang) =>
          document.documentElement.lang === lang &&
          !document.documentElement.classList.contains('i18n-wait'),
        code,
      );
      const read = await page.evaluate(readPage, LINK);
      pageLang = read.lang;
      pageDir = read.dir;
      const file = path.join(out, 'records', here, 'index.md');
      fs.mkdirSync(path.dirname(file), { recursive: true });
      fs.writeFileSync(file, resolveLinks(read.markdown, here, records, false));
      const family = here.split('/')[0];
      if (!families.has(family)) families.set(family, []);
      families.get(family).push({ path: here, html: resolveLinks(read.html, here, records, true) });
    }
    await page.close();
  }
  await Promise.all(Array.from({ length: PARALLEL }, worker));
  console.log(
    `${paths.length} Markdown files in ${((Date.now() - started) / 1000).toFixed(0)} s (${code})`,
  );

  // One PDF per top-level folder, its records in tree order, each starting on a new page.
  fs.mkdirSync(path.join(out, 'pdf'), { recursive: true });
  const printer = await context.newPage();
  const styles = PDF_STYLES.map((s) => `<link rel="stylesheet" href="${origin}/${s}">`).join('');
  for (const [family, pages] of [...families].sort()) {
    pages.sort((a, b) => (a.path < b.path ? -1 : 1));
    const body = pages
      .map(
        (p) =>
          `<article class="offline-record" id="${escapeHtml(encodeURIComponent(p.path))}">${p.html}</article>`,
      )
      .join('');
    await printer.setContent(
      `<!doctype html><html lang="${escapeHtml(pageLang)}" dir="${escapeHtml(pageDir)}"><head><meta charset="utf-8">${styles}</head><body>${body}</body></html>`,
      { waitUntil: 'load', timeout: 0 },
    );
    await printer.pdf({ path: path.join(out, 'pdf', family + '.pdf'), ...PDF_OPTIONS });
  }
  console.log(
    `${families.size} PDF files in ${((Date.now() - started) / 1000).toFixed(0)} s (${code})`,
  );

  // The terms the files come under: Lang Log's own notice, and the sources' terms that the
  // site publishes with its downloads.
  fs.copyFileSync(path.join(ROOT, 'LICENSE'), path.join(out, 'LICENSE'));
  fs.copyFileSync(
    path.join(DIST, 'signs-and-scripts-licenses.txt'),
    path.join(out, 'signs-and-scripts-licenses.txt'),
  );

  await browser.close();
  server.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
