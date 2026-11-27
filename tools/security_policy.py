"""The security policy of every page in dist/: one place for the <meta> tags.

GitHub Pages cannot send our own response headers, so the policies a browser
accepts from a <meta> element are written into the <head> of every page:

- Content-Security-Policy: only the site itself, plus https://huggingface.co
  for the model list on record pages (dist/hf-models.js). The web app manifest
  and the service worker come from the site itself. No inline scripts,
  inline styles allowed only for WebKit's <select> (see CSP), no plugins, no frames, no <base>.
- referrer: same-origin (the owner's choice, 2026-11-23): requests inside the
  site carry the full page address; nothing goes to other sites.

Policies that only work as response headers (frame-ancestors,
X-Frame-Options, Strict-Transport-Security, X-Content-Type-Options,
Permissions-Policy, Cross-Origin-*-Policy) are listed in
.claude/rules/security.md and written once below (LIVE_HEADERS). Cloudflare sends
them in front of GitHub Pages for the live site (`--live` prints them for its
Transform Rule, `--check-live <url>` checks what the site sends), and the beta
site on Cloudflare Pages sends them too: `--headers <dir>` writes <dir>/_headers
(Cloudflare's header file) from HEADERS below.

The page generators (tools/build_home.py, tools/build_paths.py) write HEAD
from here. The hand-written pages in dist/ carry the same text; run
`python3 tools/security_policy.py --write` after changing the policy.
`--check` (run by tools/build_site.sh) fails if any page in dist/ lacks the
current HEAD, has a second policy, or has a style="..." attribute or an
inline script, which the policy would block.
"""

import re
import sys
import urllib.request
from pathlib import Path

from locations import DIST


# A new script, style, image or connection source changes this list, in the
# same pull request (research-aide .claude/rules/web-security.md).
CSP = "; ".join(
    [
        "default-src 'none'",
        "script-src 'self'",
        # 'unsafe-inline' only for styles (the owner's choice, 2026-11-07): WebKit
        # reports a blocked inline stylesheet for every <select> under a strict
        # style-src, from its own rendering of the menu, not from the site. Scripts
        # stay strict, and --check still refuses style="..." in the site's own pages.
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self'",
        # The fallback fonts (tools/fallback_fonts.py: dist/fonts/, from the site itself).
        "font-src 'self'",
        "connect-src 'self' https://huggingface.co",
        # Lang Log is a progressive web app (.claude/rules/pwa.md): its manifest and its
        # service worker come from the site itself (tools/pwa.py, dist/sw.js).
        "manifest-src 'self'",
        "worker-src 'self'",
        "base-uri 'none'",
        "form-action 'self'",  # the search forms go to the search page, q
        "object-src 'none'",
        # No upgrade-insecure-requests: no source above allows http:, so it would
        # add nothing on the live HTTPS site, and WebKit applies it to
        # http://127.0.0.1, which breaks the local browser check.
    ]
)

REFERRER = "same-origin"

HEAD = (
    f'<meta http-equiv="Content-Security-Policy" content="{CSP}">'
    f'<meta name="referrer" content="{REFERRER}">'
)

# Response headers for a host that can send them (research-aide
# .claude/rules/web-security.md), used by the beta site on Cloudflare Pages
# (.claude/rules/previews.md). The beta is the production deployment of its
# Cloudflare project, which gets no noindex of its own, so it is added here.
# The response headers of the live site, sent by Cloudflare in front of GitHub Pages (one
# Response Header Transform Rule; the owner's choice, 2026-11-24, to proxy lang-log.com).
# `--live` prints them for that rule and `--check-live <url>` compares what the site sends.
LIVE_HEADERS = {
    # frame-ancestors works only as a header, so it is added to the page policy here.
    "Content-Security-Policy": f"{CSP}; frame-ancestors 'none'",
    "X-Frame-Options": "DENY",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": REFERRER,
    # Every feature the site does not use is turned off. The clipboard is left out:
    # record pages copy their address (dist/record.js).
    "Permissions-Policy": ", ".join(
        f"{feature}=()"
        for feature in [
            "accelerometer",
            "autoplay",
            "camera",
            "display-capture",
            "encrypted-media",
            "fullscreen",
            "geolocation",
            "gyroscope",
            "hid",
            "magnetometer",
            "microphone",
            "midi",
            "payment",
            "picture-in-picture",
            "publickey-credentials-get",
            "screen-wake-lock",
            "serial",
            "usb",
            "xr-spatial-tracking",
        ]
    ),
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}
# The beta site (Cloudflare Pages' _headers file, --headers): the same, and kept out of search engines.
HEADERS = {"X-Robots-Tag": "noindex", **LIVE_HEADERS}

CHARSET = '<meta charset="utf-8">'
ANY_POLICY = re.compile(
    r'<meta http-equiv="Content-Security-Policy"[^>]*>(<meta name="referrer"[^>]*>)?'
)
INLINE_STYLE = re.compile(r"<[^>]*\sstyle=")
INLINE_SCRIPT = re.compile(r'<script(?![^>]*\ssrc=)(?![^>]*type="application/ld\+json")[^>]*>')
INLINE_HANDLER = re.compile(r"<[^>]*\son[a-z]+=", re.I)


def problems(text):
    out = []
    if text.count(HEAD) != 1 or len(ANY_POLICY.findall(text)) != 1:
        out.append("does not have the current policy exactly once")
    # A <meta> policy covers only what comes after it, so it goes right after the charset.
    elif not text.startswith('<!doctype html><html lang="en"><head>' + CHARSET + HEAD):
        out.append("does not start <head> with the charset and the policy")
    if INLINE_STYLE.search(text):
        out.append('has a style="..." attribute')
    if INLINE_SCRIPT.search(text):
        out.append("has an inline script")
    if INLINE_HANDLER.search(text):
        out.append("has an inline event handler")
    if "<base" in text:
        out.append("has a <base> element")
    return out


def write(page):
    text = page.read_text(encoding="utf-8")
    new = ANY_POLICY.sub("", text).replace(CHARSET, CHARSET + HEAD, 1)
    if new != text:
        page.write_text(new, encoding="utf-8")


def write_headers(directory):
    """Write Cloudflare Pages' _headers file: every header on every path."""
    lines = ["/*"] + [f"  {name}: {value}" for name, value in HEADERS.items()]
    (Path(directory) / "_headers").write_text("\n".join(lines) + "\n", encoding="utf-8")


def check_live(url):
    """Compare the headers the live site sends with LIVE_HEADERS; the number of differences."""
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "lang-log-check"})
    with urllib.request.urlopen(request, timeout=30) as response:
        sent = response.headers
    bad = 0
    for name, value in LIVE_HEADERS.items():
        if sent.get(name) != value:
            bad += 1
            print(f"{name}: expected {value!r}, the site sends {sent.get(name)!r}")
    print(f"{url}: {len(LIVE_HEADERS) - bad} of {len(LIVE_HEADERS)} headers as in LIVE_HEADERS")
    return bad


def main(argv):
    if argv[1:] == ["--live"]:
        for name, value in LIVE_HEADERS.items():
            print(f"{name}: {value}")
        return 0
    if len(argv) == 3 and argv[1] == "--check-live":
        return 1 if check_live(argv[2]) else 0
    if len(argv) == 3 and argv[1] == "--headers":
        write_headers(argv[2])
        return 0
    if argv[1:] == ["--write"]:
        for page in sorted(DIST.glob("*.html")):
            write(page)
        return 0
    if argv[1:] != ["--check"]:
        print(
            "usage: security_policy.py --check | --write | --headers <dir> | --live | --check-live <url>",
            file=sys.stderr,
        )
        return 2
    bad = 0
    count = 0
    for page in DIST.rglob("*.html"):
        count += 1
        for p in problems(page.read_text(encoding="utf-8")):
            bad += 1
            if bad <= 20:
                print(f"{page.relative_to(DIST)}: {p}")
    # The SVG files are pages too when opened directly.
    for svg in DIST.rglob("*.svg"):
        if re.search(r"<script|\son[a-z]+=", svg.read_text(encoding="utf-8"), re.I):
            bad += 1
            print(f"{svg.relative_to(DIST)}: has a script")
    if bad:
        print(f"{bad} problems in {count} pages")
        return 1
    print(f"security policy present in all {count} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
