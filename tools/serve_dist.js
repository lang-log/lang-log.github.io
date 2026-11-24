// A static server for the built site in dist/, on 127.0.0.1 and a free port, for the scripts
// that open the built pages in a browser (tools/check_map_view.js, tools/offline_zip.js).
// Like GitHub Pages, a path that ends in "/" serves its index.html.
const http = require('http'),
  fs = require('fs'),
  path = require('path');

const DIST = path.join(__dirname, '..', 'dist');
const TYPES = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.css': 'text/css',
  '.svg': 'image/svg+xml',
  '.json': 'application/json',
  '.png': 'image/png',
  '.webmanifest': 'application/manifest+json',
};

// Resolves to the listening http.Server; its address().port is the port.
function serve() {
  const server = http.createServer((req, res) => {
    let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    if (p.endsWith('/')) p += 'index.html';
    const file = path.join(DIST, path.normalize(p));
    if (!file.startsWith(DIST) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      res.writeHead(404);
      res.end();
      return;
    }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream' });
    fs.createReadStream(file).pipe(res);
  });
  return new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve(server)));
}

module.exports = { DIST, serve };
