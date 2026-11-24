"""The site name, the owner's profile link, the copyright line and the contact line: one place for each.

Every page title ends with TITLE_SUFFIX, and "yoshi" in the header links to
PROFILE_URL (the owner's title rule: research-aide .claude/rules/titles.md and
.claude/rules/titles.md here). The page generators (tools/build_home.py,
tools/build_paths.py) write them from here. The hand-written pages in dist/
carry the same text: `--check` (run by tools/build_site.sh) fails if one of
them differs, and `--write` rewrites their "by yoshi" link and contact line from here.
Every page has one footer with the contact line (contact_line()).

dist/lang.js switches the profile link to the interface language by changing
the language part of the link's own address, so it keeps no copy of
PROFILE_URL; dist/record.js keeps the title suffix its page was built with.
"""

import json
import re
import sys
from html import escape

from locations import DIST


SITE_NAME = "Lang Log"
# The GitHub repository of the site, as <owner>/<name>: the releases are read
# from it (tools/github_api.py) and the Releases page links to it.
REPOSITORY = "lang-log/lang-log.github.io"
REPOSITORY_URL = f"https://github.com/{REPOSITORY}"
# The live site: GitHub Pages serves it at the custom domain set in the
# repository's Settings > Pages, and redirects lang-log.github.io there.
SITE_URL = "https://lang-log.com/"
# Google Search Console ownership check ("HTML tag" method; the value of
# content="..." only), written into the top page by tools/build_home.py.
GOOGLE_SITE_VERIFICATION = "vbHfV0w41tKXYEAid8L6_XhA01IqC_ekt7L6tF8P2Fo"
OWNER = "MATSUURA Yoshihiro"
HOME_TITLE = f"{SITE_NAME} by yoshi"
TITLE_SUFFIX = f" · {HOME_TITLE}"
# The English page of the personal site, with the ref that tells it where the
# visit came from (research-aide .claude/rules/profile-links.md).
PROFILE_REF = "langlog"
PROFILE_URL = f"https://nguekwang.github.io/en/?ref={PROFILE_REF}"
COPYRIGHT = f"© 2026 {OWNER}. All rights reserved."
# The contact address shown in the footer of every page (owner, 2026-11-23). Mail to it
# is forwarded to the owner by Cloudflare Email Routing.
CONTACT_EMAIL = "contact@lang-log.com"


# The favicon links every page carries, relative to the page (`up` is "../" per level).
# favicon-192.png is the same mark on the page background, square and a multiple of
# 48 px, for search engines and browsers without SVG favicons.
def icon_links(up=""):
    return (
        f'<link rel="icon" href="{up}favicon.svg" type="image/svg+xml">'
        f'<link rel="icon" href="{up}favicon-192.png" type="image/png" sizes="192x192">'
        f'<link rel="apple-touch-icon" href="{up}apple-touch-icon.png">'
    )


# The site name for link previews and search engines.
SITE_NAME_META = f'<meta property="og:site_name" content="{escape(SITE_NAME)}">'


# The WebSite structured data on the top page, which search engines read for the
# site name they show above a result. "<" is escaped so the JSON cannot end the script.
WEBSITE_JSONLD = (
    '<script type="application/ld+json">'
    + json.dumps(
        {"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": SITE_URL},
        ensure_ascii=False,
    ).replace("<", "\\u003c")
    + "</script>"
)


# The query tools/version_assets.py adds to asset links.
ASSET_VERSION = re.compile(r"\?v=[0-9a-f]+")


# Any "by yoshi" link in a page, whatever its attributes.
ANY_BY = re.compile(r'<(span|p) class="(by|home-by)">by <a [^>]*>yoshi</a></\1>')


# Any contact line in a page, whatever its address.
ANY_CONTACT = re.compile(r'<(span|p) class="contact">Contact: <a [^>]*>[^<]*</a></\1>')


def by_yoshi(tag="span", cls="by"):
    """The "by yoshi" line; "yoshi" links to the profile (class "profile", for dist/lang.js)."""
    link = f'<a class="profile" href="{escape(PROFILE_URL)}" title="{escape(OWNER)}">yoshi</a>'
    return f'<{tag} class="{cls}">by {link}</{tag}>'


def contact_line(tag="span"):
    """The footer's contact line. "Contact:" is translated by dist/lang.js; the address is not."""
    address = escape(CONTACT_EMAIL)
    return (
        f'<{tag} class="contact">Contact: '
        f'<a class="notranslate" href="mailto:{address}" dir="ltr">{address}</a></{tag}>'
    )


def problems(text):
    out = []
    if text.count(by_yoshi()) != 1 or len(ANY_BY.findall(text)) != 1:
        out.append('does not have the current "by yoshi" link exactly once')
    if text.count("<footer") != 1 or text.count(CONTACT_EMAIL) != 2 or contact_line() not in text:
        out.append("does not have one footer with the current contact line (contact_line())")
    title = re.search(r"<title>([^<]*)</title>", text)
    if not title or not title.group(1).endswith(TITLE_SUFFIX.strip()):
        out.append(f'has a title that does not end with "{TITLE_SUFFIX.strip()}"')
    # tools/version_assets.py adds ?v=<hash> to the SVG link in CI; compare without it.
    links = ASSET_VERSION.sub("", text)
    if links.count(icon_links()) + links.count(icon_links("/")) != 1:
        out.append("does not have the current favicon links (icon_links()) exactly once")
    if text.count(SITE_NAME_META) != 1:
        out.append("does not have the og:site_name tag (SITE_NAME_META) exactly once")
    return out


def main(argv):
    pages = sorted(DIST.glob("*.html"))
    if argv[1:] == ["--write"]:
        for page in pages:
            text = page.read_text(encoding="utf-8")
            new = ANY_BY.sub(lambda m: by_yoshi(m.group(1), m.group(2)), text)
            new = ANY_CONTACT.sub(lambda m: contact_line(m.group(1)), new)
            if new != text:
                page.write_text(new, encoding="utf-8")
        return 0
    if argv[1:] != ["--check"]:
        print("usage: site_brand.py --check | --write", file=sys.stderr)
        return 2
    bad = 0
    for page in pages:
        if page.name == "index.html":  # written by build_home.py from here
            continue
        for p in problems(page.read_text(encoding="utf-8")):
            bad += 1
            print(f"dist/{page.name}: {p}")
    if bad:
        print("run: python3 tools/site_brand.py --write")
        return 1
    print(f"site name and profile link as in tools/site_brand.py in {len(pages)} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
