"""Tests for the Releases page and the release tools (tools/build_releases.py,
tools/github_api.py, tools/release.py). No network: API answers are made up here.

Run from the repository root (tools/build_site.sh does):
    python3 -m unittest discover -s tools -p 'test_*.py'
"""

import contextlib
import io
import json
import os
import re
import subprocess
import tempfile
import unittest
import urllib.error
from email.message import Message

import build_releases as br
import github_api
import info_page
import release
from security_policy import problems as policy_problems
from site_brand import REPOSITORY_URL

GH = "https://github.com/lang-log/lang-log.github.io"


def rel(tag, **kw):
    """One release as the API gives it."""
    r = {
        "tag_name": tag,
        "name": f"Lang Log {tag}",
        "draft": False,
        "prerelease": False,
        "published_at": "2026-11-08T03:00:00Z",
        "html_url": f"{GH}/releases/tag/{tag}",
        "body": "## Changes\n\n- one",
        "body_html": "<h2>Changes</h2><ul><li>one</li></ul>",
        "assets": [],
    }
    r.update(kw)
    return r


def page(releases):
    return info_page.page("Releases", br.page_body(releases), "")


class Sanitize(unittest.TestCase):
    def test_keeps_markdown_structure(self):
        html = '<h2>What\'s Changed</h2><ul><li><a href="https://github.com/x/y/pull/1">#1</a> by <strong>a</strong></li></ul><pre><code>x &lt; y</code></pre>'
        self.assertEqual(
            br.sanitize(html),
            '<h4>What&#x27;s Changed</h4><ul><li><a href="https://github.com/x/y/pull/1">#1</a>'
            " by <strong>a</strong></li></ul><pre><code>x &lt; y</code></pre>",
        )

    def test_removes_scripts_and_handlers(self):
        cases = [
            "<script>alert(1)</script>ok",
            '<img src="x" onerror="alert(1)" alt="ok">',
            '<a href="javascript:alert(1)">ok</a>',
            '<a href="data:text/html,<script>alert(1)</script>">ok</a>',
            '<p style="color:red" onclick="alert(1)">ok</p>',
            "<iframe src=//evil></iframe>ok",
            "<svg><script>alert(1)</script></svg>ok",
            "<style>body{}</style>ok",
            '<a href="https://evil.example/">ok</a>',
            '<a href="https://github.com/a onclick=alert(1)">ok</a>',
            "<scr<script>ipt>alert(1)</script>ok",
            "<!-- <script>alert(1)</script> -->ok",
            '<form action="x"><input value="y"></form>ok',
            '<input onfocus="alert(1)" autofocus>ok',
            "<base href=//evil>ok",
            "<math><mi>x</mi></math>ok",
        ]
        for c in cases:
            with self.subTest(c=c):
                out = br.sanitize(c)
                self.assertIn("ok", out)
                self.assertNotRegex(
                    out.lower(), r"<script|<iframe|<svg|<style|<img|<form|<input|<base|<math"
                )
                self.assertNotRegex(out.lower(), r"\son[a-z]+=|\sstyle=|javascript:|data:text")
                self.assertNotIn("evil", out.split("ok")[0] if "href" in out else "")
                for href in re.findall(r'href="([^"]*)"', out):
                    self.assertTrue(href.startswith("https://github.com/"), href)

    def test_text_is_escaped(self):
        self.assertEqual(
            br.sanitize('&lt;b&gt;x&lt;/b&gt; & "q"'), "&lt;b&gt;x&lt;/b&gt; &amp; &quot;q&quot;"
        )

    def test_unbalanced_tags_are_closed(self):
        self.assertEqual(br.sanitize("<ul><li>a<li>b"), "<ul><li>a<li>b</li></li></ul>")
        self.assertEqual(br.sanitize("</p></div>text"), "text")

    def test_headings_stay_below_the_release_name(self):
        self.assertEqual(br.sanitize("<h1>a</h1><h5>b</h5>"), "<h3>a</h3><h6>b</h6>")


class Normalize(unittest.TestCase):
    def test_none(self):
        self.assertEqual(br.normalize({"releases": [], "latest": None}), [])
        html = page([])
        self.assertIn("No releases yet.", html)
        self.assertNotIn('class="releases"', html)

    def test_one(self):
        out = br.normalize({"releases": [rel("v1.0.0")], "latest": "v1.0.0"})
        self.assertEqual(len(out), 1)
        r = out[0]
        self.assertEqual((r["tag"], r["name"], r["latest"]), ("v1.0.0", "Lang Log v1.0.0", True))
        self.assertEqual(r["notes"], "## Changes\n\n- one")
        html = page(out)
        self.assertIn('<span class="release-badge">Latest</span>', html)
        self.assertIn(f'href="{GH}/releases/tag/v1.0.0">View on GitHub</a>', html)
        self.assertIn('<time datetime="2026-11-08T03:00:00Z">8 Nov 2026</time>', html)
        self.assertIn(f'href="{REPOSITORY_URL}/releases">All releases on GitHub', html)

    def test_many_newest_first_and_drafts_left_out(self):
        out = br.normalize(
            {
                "releases": [
                    rel("v1.0.0", published_at="2026-01-01T00:00:00Z"),
                    rel("v2.0.0", published_at="2026-03-01T00:00:00Z"),
                    rel("v1.1.0", published_at="2026-02-01T00:00:00Z", prerelease=True),
                    rel("v3.0.0", draft=True),
                    rel("v1.1.0"),  # the same tag twice: the first one counts
                ],
                "latest": "v2.0.0",
            }
        )
        self.assertEqual([r["tag"] for r in out], ["v2.0.0", "v1.1.0", "v1.0.0"])
        self.assertEqual([r["latest"] for r in out], [True, False, False])
        html = page(out)
        self.assertEqual(html.count('class="release-badge">Latest'), 1)
        self.assertIn("Pre-release", html)
        self.assertNotIn("v3.0.0", html)

    def test_assets(self):
        assets = [
            {"name": "atlas.zip", "browser_download_url": f"{GH}/releases/download/v1.0.0/atlas.zip", "size": 2048, "content_type": "application/zip"},
            {"name": "evil.zip", "browser_download_url": "https://evil.example/x.zip"},
            {"name": "", "browser_download_url": f"{GH}/releases/download/v1.0.0/x"},
            "not an asset",
        ]  # fmt: skip
        r = br.normalize({"releases": [rel("v1.0.0", assets=assets)], "latest": None})[0]
        self.assertEqual([a["name"] for a in r["assets"]], ["atlas.zip"])
        self.assertEqual(r["assets"][0]["size"], 2048)
        html = page([r])
        self.assertIn("<h3>Downloads</h3>", html)
        self.assertIn(f'href="{GH}/releases/download/v1.0.0/atlas.zip">atlas.zip</a>', html)
        self.assertNotIn("evil", html)

    def test_missing_metadata(self):
        r = br.normalize(
            {
                "releases": [
                    {"tag_name": "v1.0.0"},
                    {"name": "no tag"},
                    None,
                    {"tag_name": "v0.9.0", "name": 5, "published_at": "not a date", "html_url": "http://github.com/x", "body": None, "assets": "x"},
                ],
                "latest": 7,
            }
        )  # fmt: skip
        self.assertEqual([x["tag"] for x in r], ["v1.0.0", "v0.9.0"])
        for x in r:
            self.assertEqual(x["name"], x["tag"])
            self.assertIsNone(x["published"])
            self.assertIsNone(x["url"])
            self.assertFalse(x["latest"])
            self.assertEqual(x["assets"], [])
        html = page(r)
        self.assertIn("Date unknown", html)
        self.assertIn("No release notes.", html)
        self.assertNotIn("View on GitHub", html)

    def test_markdown_without_html(self):
        r = br.normalize(
            {
                "releases": [rel("v1.0.0", body_html=None, body="<script>x</script>\n- a")],
                "latest": None,
            }
        )
        html = page(r)
        self.assertIn("&lt;script&gt;x&lt;/script&gt;\n- a", html)
        self.assertNotIn("<script>x", html)

    def test_bad_answers(self):
        for bad in (None, [], {"releases": {}}, {"latest": None}, "x"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                br.normalize(bad)

    def test_hostile_names(self):
        r = br.normalize(
            {
                "releases": [
                    rel(
                        'v1"><script>alert(1)</script>',
                        name="<img src=x onerror=alert(1)>",
                        body_html='<p onmouseover="alert(1)">x</p><script>alert(2)</script>',
                        assets=[{"name": "<b>a</b>", "browser_download_url": f"{GH}/a"}],
                    )
                ],
                "latest": None,
            }
        )
        html = page(r)
        self.assertEqual(policy_problems(html), [])
        body = html.split("<main", 1)[1]
        # Only escaped text is left: no element and no attribute from the release.
        self.assertNotRegex(body, r"<script|<img|<b>|<[^>]*\son[a-z]+=")


class PageShell(unittest.TestCase):
    def test_policy_and_relative_links(self):
        html = page([])
        self.assertEqual(policy_problems(html), [])
        self.assertIn('<link rel="stylesheet" href="style.css">', html)
        self.assertIn('<a class="home" href="./">', html)
        self.assertIn("<title>Releases · Lang Log by yoshi</title>", html)


class FakeResponse(io.BytesIO):
    def __init__(self, body, status=200, headers=None):
        super().__init__(json.dumps(body).encode())
        self.status = status
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def http_error(code, headers=None):
    msg = Message()
    for k, v in (headers or {}).items():
        msg[k] = v
    return urllib.error.HTTPError("https://api.github.com/x", code, "error", msg, io.BytesIO(b""))


class Api(unittest.TestCase):
    def test_fetch_pages_and_latest(self):
        calls = []
        nxt = "https://api.github.com/repositories/1/releases?per_page=100&page=2"

        def opener(req, timeout):
            calls.append(req.full_url)
            if req.full_url.endswith("/releases/latest"):
                return FakeResponse(rel("v2.0.0"))
            if "page=2" in req.full_url:
                return FakeResponse([rel("v1.0.0")])
            return FakeResponse([rel("v2.0.0")], headers={"Link": f'<{nxt}>; rel="next"'})

        data = br.fetch(opener=opener)
        self.assertEqual([r["tag_name"] for r in data["releases"]], ["v2.0.0", "v1.0.0"])
        self.assertEqual(data["latest"], "v2.0.0")
        self.assertEqual(len(calls), 3)

    def test_no_latest_is_fine(self):
        def opener(req, timeout):
            if req.full_url.endswith("/releases/latest"):
                raise http_error(404)
            return FakeResponse([])

        self.assertEqual(br.fetch(opener=opener), {"releases": [], "latest": None})

    def test_rate_limit_waits_then_works(self):
        waits, tries = [], []

        def opener(req, timeout):
            tries.append(1)
            if len(tries) == 1:
                raise http_error(403, {"X-RateLimit-Remaining": "0", "Retry-After": "3"})
            return FakeResponse([])

        self.assertEqual(
            github_api.get_all("/repos/a/b/releases", opener=opener, sleep=waits.append), []
        )
        self.assertEqual(waits, [3])

    def test_long_rate_limit_fails(self):
        def opener(req, timeout):
            raise http_error(429, {"Retry-After": str(github_api.MAX_WAIT_S + 1)})

        with self.assertRaises(github_api.ApiError):
            github_api.get_all("/x", opener=opener, sleep=lambda s: None)

    def test_errors_and_bad_answers(self):
        cases = [
            lambda req, timeout: (_ for _ in ()).throw(http_error(500)),
            lambda req, timeout: (_ for _ in ()).throw(http_error(401)),
            lambda req, timeout: FakeResponse({"message": "not a list"}),
        ]
        for opener in cases:
            with self.assertRaises(github_api.ApiError):
                github_api.get_all("/x", opener=opener, sleep=lambda s: None)

    def test_not_json(self):
        class Raw(FakeResponse):
            def read(self):
                return b"<html>"

        with self.assertRaises(github_api.ApiError):
            github_api.request("GET", "/x", opener=lambda req, timeout: Raw(None))

    def test_token_only_to_the_api(self):
        with self.assertRaises(github_api.ApiError):
            github_api.request("GET", "https://evil.example/x", opener=lambda *a, **k: self.fail())
        sent = []

        def opener(req, timeout):
            sent.append(req.get_header("Authorization"))
            return FakeResponse([], headers={"Link": '<https://evil.example/next>; rel="next"'})

        env = dict(github_api.os.environ)
        try:
            github_api.os.environ["GITHUB_TOKEN"] = "secret"
            with self.assertRaises(github_api.ApiError):
                github_api.get_all("/x", opener=opener, sleep=lambda s: None)
        finally:
            github_api.os.environ.clear()
            github_api.os.environ.update(env)
        self.assertEqual(sent, ["Bearer secret"])


class VersionTags(unittest.TestCase):
    def test_semver(self):
        for good in ("v1.0.0", "v1.1.0", "v1.1.1", "v2.0.0", "v0.1.0", "v10.20.30"):
            self.assertTrue(release.VERSION_TAG.fullmatch(good), good)
        for bad in (
            "1.0.0",
            "v1.0",
            "v01.0.0",
            "v1.0.0-rc.1",
            "v1.0.0+b",
            "v1.0.0\n",
            "vx.y.z",
            "v1.0.0 ",
        ):
            self.assertFalse(release.VERSION_TAG.fullmatch(bad), bad)


class CheckTag(unittest.TestCase):
    """release.check_tag() on a small repository: main with two commits, one more off main."""

    def setUp(self):
        self.old = os.getcwd()
        self.dir = tempfile.TemporaryDirectory()
        os.chdir(self.dir.name)
        who = {"NAME": "t", "EMAIL": "t@example.invalid"}
        env = {
            **os.environ,
            **{f"GIT_{r}_{k}": v for r in ("AUTHOR", "COMMITTER") for k, v in who.items()},
        }

        def git(*a):
            subprocess.run(["git", *a], check=True, capture_output=True, env=env)

        git("init", "-q", "-b", "main")
        git("commit", "-q", "--allow-empty", "-m", "one")
        git("tag", "-a", "v1.0.0", "-m", "First release", "-m", "Details.")
        git("tag", "v1.0.1")  # lightweight
        git("update-ref", "refs/remotes/origin/main", "HEAD")
        git("checkout", "-q", "-b", "side")
        git("commit", "-q", "--allow-empty", "-m", "off main")
        git("tag", "-a", "v9.0.0", "-m", "not on main")

    def tearDown(self):
        os.chdir(self.old)
        self.dir.cleanup()

    def test_annotated_tag_on_main(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            sha = release.check_tag("v1.0.0")
        self.assertRegex(sha, r"^[0-9a-f]{40}$")
        self.assertEqual(out.getvalue(), "")
        self.assertEqual(release.tag_message("v1.0.0"), "First release\n\nDetails.")

    def test_lightweight_tag_warns(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            release.check_tag("v1.0.1")
        self.assertIn("::warning::", out.getvalue())
        self.assertEqual(release.tag_message("v1.0.1"), "")

    def test_refused(self):
        for tag in ("v9.0.0", "v2.0.0", "v1.0", "main"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                release.check_tag(tag)


if __name__ == "__main__":
    unittest.main()
