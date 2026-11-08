"""Write dist/sitemap.xml and dist/robots.txt for search engines.

The sitemap lists every page in dist/ that search engines may index: every
.html file except those marked <meta name="robots" content="noindex"> (such as
404.html and q.html). A page at <dir>/index.html is listed as <dir>/, the
address the site links to. The sitemap protocol allows MAX_URLS addresses per
file; when there are more, the pages go into sitemap-<n>.xml files and
sitemap.xml becomes their index. robots.txt lets every crawler in and names
the sitemap.

Both are rebuilt from dist/ on every build (tools/build_site.sh) and are not
committed. Run it after every page is written.
"""

import sys
from xml.sax.saxutils import escape

from locations import DIST
from site_brand import SITE_URL

# The sitemap protocol's limit of addresses in one file
# (https://www.sitemaps.org/protocol.html).
MAX_URLS = 50000
SITEMAP = "sitemap.xml"
NOINDEX = '<meta name="robots" content="noindex">'
XML_HEAD = '<?xml version="1.0" encoding="UTF-8"?>\n'
XMLNS = 'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'


def page_urls():
    urls = []
    for page in sorted(DIST.rglob("*.html")):
        if NOINDEX in page.read_text(encoding="utf-8"):
            continue
        path = page.relative_to(DIST).as_posix()
        if path == "index.html" or path.endswith("/index.html"):
            path = path[: -len("index.html")]
        urls.append(SITE_URL + path)
    return urls


def write_list(name, tag, urls):
    body = "".join(f"<{tag}><loc>{escape(url)}</loc></{tag}>\n" for url in urls)
    root = "urlset" if tag == "url" else "sitemapindex"
    text = f"{XML_HEAD}<{root} {XMLNS}>\n{body}</{root}>\n"
    (DIST / name).write_text(text, encoding="utf-8")


def main():
    for old in DIST.glob("sitemap*.xml"):
        old.unlink()
    urls = page_urls()
    if not urls:
        sys.exit("build_sitemap.py: no indexable pages in dist/")
    if len(urls) <= MAX_URLS:
        write_list(SITEMAP, "url", urls)
        files = [SITEMAP]
    else:
        parts = [urls[i : i + MAX_URLS] for i in range(0, len(urls), MAX_URLS)]
        files = [f"sitemap-{n}.xml" for n in range(1, len(parts) + 1)]
        for name, part in zip(files, parts, strict=True):
            write_list(name, "url", part)
        write_list(SITEMAP, "sitemap", [SITE_URL + name for name in files])
    robots = f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}{SITEMAP}\n"
    (DIST / "robots.txt").write_text(robots, encoding="utf-8")
    print(f"build_sitemap.py: {len(urls)} pages in {', '.join(files)}")


if __name__ == "__main__":
    main()
