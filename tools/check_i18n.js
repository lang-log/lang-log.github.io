// Checks that every interface language in dist/lang.js has a complete dictionary:
// dist/i18n.js for Japanese, dist/i18n/<code>.js for the others. Each must have every
// exact string and every pattern of the Japanese block, with no empty translation.
// Strings the Japanese block lacks are allowed (a dictionary may already hold the text of
// a page that another pull request adds).
// Run from the repository root: node tools/check_i18n.js
const fs = require('fs'),
  path = require('path'),
  dist = path.join(__dirname, '..', 'dist');
const read = (f) => fs.readFileSync(path.join(dist, f), 'utf8');
const window = {};
new Function('window', read('i18n.js'))(window);
const lang = read('lang.js');
const table = lang.match(/var LANGS = \[([\s\S]*?)\];/);
if (!table) {
  console.error('lang.js: LANGS table not found');
  process.exit(1);
}
const codes = [...table[1].matchAll(/\['([A-Za-z-]+)'/g)].map((m) => m[1]);
const errors = [];
for (const code of codes) {
  if (code === 'en' || code === 'ja') continue;
  const file = path.join('i18n', code + '.js');
  if (!fs.existsSync(path.join(dist, file))) {
    errors.push('missing dist/' + file);
    continue;
  }
  new Function('window', read(file))(window);
}
const ja = window.LANGLOG_I18N.ja;
if (!ja) errors.push('dist/i18n.js has no ja block');
for (const code of codes) {
  if (code === 'en' || !ja) continue;
  const d = window.LANGLOG_I18N[code];
  if (!d) {
    errors.push(code + ': no dictionary');
    continue;
  }
  if (typeof d.join !== 'string') errors.push(code + ': join is not a string');
  for (const k of Object.keys(ja.exact)) {
    if (!(k in d.exact)) errors.push(code + ': missing exact ' + JSON.stringify(k));
    else if (typeof d.exact[k] !== 'string' || !d.exact[k].trim())
      errors.push(code + ': empty exact ' + JSON.stringify(k));
  }
  const want = ja.patterns.map((p) => p[0].source),
    have = (d.patterns || []).map((p) => p[0].source);
  for (const s of want) if (!have.includes(s)) errors.push(code + ': missing pattern /' + s + '/');
}
if (errors.length) {
  console.error(errors.join('\n'));
  process.exit(1);
}
console.log(
  'i18n: ' +
    (codes.length - 1) +
    ' dictionaries, ' +
    Object.keys(ja.exact).length +
    ' strings and ' +
    ja.patterns.length +
    ' patterns each',
);
