"""Write the Releases page, dist/releases.html, and its data, dist/releases.json.

GitHub Releases are the record of every Lang Log release (the owner's
decision, 2026-11-08; .claude/rules/releases.md): pushing a version tag such as
v1.2.0 makes .github/workflows/release.yml create the release (tools/release.py),
and the site shows what GitHub holds. Nothing here is written by hand or by an
AI; the page is rebuilt from the GitHub API on every build.

Two steps, so the API is read with a token that can only read:

- `--fetch`: read every release and the latest one from the API and save the
  answer as it came in FETCHED (build/, not committed). pages.yml does this in
  a job of its own with `contents: read` and hands the file to the deployment;
  site.yml does it before the build.
- no argument (tools/build_site.sh): read FETCHED, or the API when the file is
  not there (local builds and the browser check), then write the page and the
  JSON. A broken answer or an unreachable API stops the build, so a deployment
  never replaces the live page with an empty one.

Release notes, names and asset names are untrusted text. The page shows the
notes as GitHub renders their Markdown (body_html), passed through sanitize(),
which keeps only plain formatting tags and https:// links into GitHub and
escapes everything else; dist/releases.json keeps the Markdown (body) as it is.
"""

import datetime
import json
import re
import sys
from html import escape
from html.parser import HTMLParser

import github_api
import info_page
from locations import DIST, ROOT
from site_brand import REPOSITORY_URL

# The API answer saved by --fetch. pages.yml uploads and downloads this file by
# its folder and name (the artifact "github-releases"); keep the two equal.
FETCHED = ROOT / "build" / "github-releases.json"
PAGE = DIST / "releases.html"
DATA = DIST / "releases.json"
# The answer of the API with both the Markdown and GitHub's HTML of each body.
ACCEPT_FULL = "application/vnd.github.full+json"
# Links in the notes and on the page may only go to this repository on GitHub.
LINK_PREFIX = "https://github.com/"
# The release-note headings sit under the release name (<h2>), so an <h1> in
# the notes becomes an <h3>; nothing goes below <h6>.
HEADING_SHIFT = 2
DEEPEST_HEADING = 6

# Tags kept in the notes, without any attribute (only href on <a>).
KEEP = {
    "p", "br", "hr", "ul", "ol", "li", "blockquote", "pre", "code", "em", "strong",
    "b", "i", "del", "s", "sup", "sub", "kbd", "table", "thead", "tbody", "tr",
    "th", "td", "details", "summary", "dl", "dt", "dd", "a",
    "h1", "h2", "h3", "h4", "h5", "h6",
}  # fmt: skip
VOID = {"br", "hr"}
# Tags removed together with everything inside them. Only tags that have an end
# tag: a void element such as <input> is simply not kept. If an end tag is
# missing, the rest of the notes is left out, never shown unescaped.
DROP = {
    "script", "style", "iframe", "frameset", "object", "applet", "svg", "math",
    "template", "noscript", "textarea", "select", "button", "form", "head",
    "title", "video", "audio", "canvas", "map",
}  # fmt: skip


def safe_link(url):
    """`url` if it is an https:// address on GitHub with no spaces or quotes, else None."""
    if not isinstance(url, str) or not url.startswith(LINK_PREFIX):
        return None
    if re.search(r"[\s\"'<>`\\]", url):
        return None
    return url


class _Sanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.open = []  # the kept tags still open, as written to out
        self.dropping = 0  # depth inside DROP tags

    def _tag(self, tag):
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            return f"h{min(int(tag[1]) + HEADING_SHIFT, DEEPEST_HEADING)}"
        return tag

    def handle_starttag(self, tag, attrs):
        if tag in DROP:
            self.dropping += 1
            return
        if self.dropping:
            return
        if tag == "img":
            # Images would load from outside the site (the policy allows only the
            # site itself); show the alternative text instead.
            alt = dict(attrs).get("alt") or ""
            self.out.append(escape(alt))
            return
        if tag not in KEEP:
            return
        out = self._tag(tag)
        if tag == "a":
            href = safe_link(dict(attrs).get("href"))
            self.out.append(f'<a href="{escape(href)}">' if href else "<a>")
        else:
            self.out.append(f"<{out}>")
        if tag not in VOID:
            self.open.append(out)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag in DROP:
            self.dropping -= 1
        elif tag in KEEP and tag not in VOID and not self.dropping:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in DROP:
            self.dropping = max(0, self.dropping - 1)
            return
        if self.dropping or tag not in KEEP or tag in VOID:
            return
        out = self._tag(tag)
        if out not in self.open:
            return
        while self.open:
            last = self.open.pop()
            self.out.append(f"</{last}>")
            if last == out:
                break

    def handle_data(self, data):
        if not self.dropping:
            self.out.append(escape(data))

    def close(self):
        super().close()
        while self.open:
            self.out.append(f"</{self.open.pop()}>")


def sanitize(html):
    """Release notes as HTML that is safe to put in the page."""
    s = _Sanitizer()
    s.feed(html)
    s.close()
    return "".join(s.out)


def _text(value):
    """`value` as stripped text, or "" when it is not a string."""
    return value.strip() if isinstance(value, str) else ""


def _time(value):
    """An ISO 8601 time from the API as an aware datetime, or None."""
    try:
        return datetime.datetime.fromisoformat(_text(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _asset(a):
    if not isinstance(a, dict):
        return None
    name, url = _text(a.get("name")), safe_link(a.get("browser_download_url"))
    if not name or not url:
        return None
    size = a.get("size")
    return {
        "name": name,
        "url": url,
        "size": size if isinstance(size, int) and size >= 0 else None,
        "contentType": _text(a.get("content_type")) or None,
    }


def normalize(fetched):
    """The releases to show, newest first, from the saved API answer.

    `fetched` is {"releases": [...], "latest": "<tag>" or None}. Raises ValueError
    when its shape is wrong; a single broken release is left out with a warning.
    Drafts are left out: they are not published.
    """
    if not isinstance(fetched, dict) or not isinstance(fetched.get("releases"), list):
        raise ValueError("the release list is missing or is not a list")
    latest = fetched.get("latest")
    latest = latest if isinstance(latest, str) else None
    out, seen = [], set()
    for i, r in enumerate(fetched["releases"]):
        tag = _text(r.get("tag_name")) if isinstance(r, dict) else ""
        if not tag:
            print(f"release {i}: no tag, left out", file=sys.stderr)
            continue
        if r.get("draft") is True or tag in seen:
            continue
        seen.add(tag)
        published = _time(r.get("published_at")) or _time(r.get("created_at"))
        assets = r.get("assets") if isinstance(r.get("assets"), list) else []
        out.append(
            {
                "name": _text(r.get("name")) or tag,
                "tag": tag,
                "published": published.astimezone(datetime.timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
                if published
                else None,
                "url": safe_link(r.get("html_url")),
                "prerelease": r.get("prerelease") is True,
                "latest": tag == latest,
                "notes": r.get("body") if isinstance(r.get("body"), str) else "",
                "notesHtml": sanitize(r["body_html"])
                if isinstance(r.get("body_html"), str)
                else None,
                "assets": [x for x in map(_asset, assets) if x],
            }
        )
    # Newest first; releases without a date go last, in the API's order.
    out.sort(key=lambda r: r["published"] or "", reverse=True)
    return out


def _anchor(tag):
    """An id for a release's <li>, from its tag (v1.2.0 -> v1-2-0)."""
    return re.sub(r"[^A-Za-z0-9_-]+", "-", tag).strip("-")


def release_html(r):
    badges = ""
    if r["latest"]:
        badges += ' <span class="release-badge">Latest</span>'
    if r["prerelease"]:
        badges += ' <span class="release-badge release-pre">Pre-release</span>'
    if r["published"]:
        day = datetime.date.fromisoformat(r["published"][:10])
        when = f'<time datetime="{escape(r["published"])}">{day.day} {day.strftime("%b %Y")}</time>'
    else:
        when = "<span>Date unknown</span>"
    # The tag is shown when the name does not already say it.
    meta = [when] if r["name"] == r["tag"] else [f"<code>{escape(r['tag'])}</code>", when]
    if r["url"]:
        meta.append(f'<a href="{escape(r["url"])}">View on GitHub</a>')
    # The notes and the name are data in their own language: dir="auto" keeps English notes
    # left to right on an Arabic or Persian page.
    if r["notesHtml"]:
        notes = f'<div class="release-notes notranslate" dir="auto">{r["notesHtml"]}</div>'
    elif r["notes"].strip():
        # No HTML from GitHub: show the Markdown as plain text, line breaks kept.
        notes = f'<div class="release-notes release-plain notranslate" dir="auto">{escape(r["notes"])}</div>'
    else:
        notes = '<p class="muted">No release notes.</p>'
    files = ""
    if r["assets"]:
        rows = "".join(
            f'<li><a class="notranslate" href="{escape(a["url"])}">{escape(a["name"])}</a></li>'
            for a in r["assets"]
        )
        files = f'<h3>Downloads</h3><ul class="release-assets">{rows}</ul>'
    anchor = _anchor(r["tag"])
    return (
        f'<li class="release{" release-latest" if r["latest"] else ""}"'
        + (f' id="{escape(anchor)}"' if anchor else "")
        + f'><h2><span class="notranslate" dir="auto">{escape(r["name"])}</span>{badges}</h2>'
        f'<p class="release-meta">{" · ".join(meta)}</p>{notes}{files}</li>'
    )


def page_body(releases):
    head = f'<p class="release-all"><a href="{escape(REPOSITORY_URL)}/releases">All releases on GitHub</a></p>'
    if not releases:
        return head + '<p class="muted">No releases yet.</p>'
    return head + f'<ol class="releases">{"".join(release_html(r) for r in releases)}</ol>'


def fetch(opener=None, sleep=None):
    """The releases and the latest release's tag, from the GitHub API."""
    kw = {"opener": opener}
    if sleep:
        kw["sleep"] = sleep
    releases = github_api.get_all(github_api.repo_path("/releases"), accept=ACCEPT_FULL, **kw)
    try:
        _, _, latest = github_api.request("GET", github_api.repo_path("/releases/latest"), **kw)
    except github_api.ApiError as e:
        if e.status != 404:  # 404: no published release yet
            raise
        latest = None
    tag = latest.get("tag_name") if isinstance(latest, dict) else None
    return {"releases": releases, "latest": tag if isinstance(tag, str) else None}


def build(fetched):
    releases = normalize(fetched)
    DATA.write_text(
        json.dumps({"releases": releases}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    PAGE.write_text(info_page.page("Releases", page_body(releases), ""), encoding="utf-8")
    return releases


def main(argv):
    try:
        if argv[1:] == ["--fetch"]:
            FETCHED.parent.mkdir(exist_ok=True)
            data = fetch()
            FETCHED.write_text(json.dumps(data), encoding="utf-8")
            print(f"{len(data['releases'])} releases read from the API")
            return 0
        if argv[1:]:
            print("usage: build_releases.py [--fetch]", file=sys.stderr)
            return 2
        if FETCHED.exists():
            fetched = json.loads(FETCHED.read_text(encoding="utf-8"))
        else:
            print(f"{FETCHED.relative_to(ROOT)} not found: reading the API", file=sys.stderr)
            fetched = fetch()
        releases = build(fetched)
    except (github_api.ApiError, ValueError) as e:
        print(f"releases: {e}", file=sys.stderr)
        return 1
    print(f"releases page: {len(releases)} releases")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
