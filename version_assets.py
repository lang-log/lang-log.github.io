"""Add a content version to every local CSS, JS and SVG link in dist/*.html.

GitHub Pages serves every file with a ten-minute browser cache
(max-age=600). After a deploy, a browser could pair the new HTML with the
style.css or script it cached from the previous deploy, and the page looked
broken until the cache ran out. This script rewrites, for example,
href="style.css" to href="style.css?v=<hash>", where the hash comes from the
file's content, so a changed file always has a new address and an unchanged
one keeps its cache.

Run it last in the build, after every page has been written. It runs only in
CI; the HTML files committed in dist/ keep plain links.
"""
import hashlib
import re
from pathlib import Path

DIST = Path(__file__).resolve().parent / "dist"

# href="..." or src="..." pointing at a relative .css, .js or .svg file,
# with an optional #fragment (logo.svg#logo). Absolute URLs, data: URIs and
# links that already carry a query are left alone.
LINK = re.compile(r'\b(href|src)="((?:\.\./)*[A-Za-z0-9_./-]+\.(?:css|js|svg))(#[^"?]*)?"')

_versions = {}


def version(path):
    if path not in _versions:
        _versions[path] = hashlib.sha256(path.read_bytes()).hexdigest()[:10] if path.is_file() else None
    return _versions[path]


def rewrite(page):
    text = page.read_text(encoding="utf-8")

    def sub(m):
        attr, url, frag = m.group(1), m.group(2), m.group(3) or ""
        v = version((page.parent / url).resolve())
        if v is None:
            return m.group(0)
        return f'{attr}="{url}?v={v}{frag}"'

    new = LINK.sub(sub, text)
    if new != text:
        page.write_text(new, encoding="utf-8")
        return True
    return False


def main():
    changed = sum(rewrite(p) for p in DIST.rglob("*.html"))
    print(f"versioned asset links in {changed} pages")


if __name__ == "__main__":
    main()
