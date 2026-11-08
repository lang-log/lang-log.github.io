"""A small client for the GitHub REST API, with the standard library only.

Used by tools/release.py (creates a release when a version tag is pushed) and
tools/build_releases.py (reads the releases for the Releases page). The token
comes from the GITHUB_TOKEN environment variable, which GitHub Actions gives
each job with the permissions its workflow sets; without it, requests are
anonymous (fine for local builds, with a lower rate limit). The token is only
ever sent to API_HOST and is never printed.

Every response is untrusted input: callers check its shape before using it.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from site_brand import REPOSITORY

API_HOST = "api.github.com"
API = f"https://{API_HOST}"
API_VERSION = "2022-11-28"
# Seconds to wait for one response before giving up on it.
TIMEOUT_S = 30
# Tries per request: the first one and the retries after a rate limit or a
# server error.
ATTEMPTS = 4
# Longest wait between two tries, in seconds. A rate limit that resets later
# than this fails the run instead of holding the job.
MAX_WAIT_S = 120
# Releases per page of the list (the API's maximum).
PER_PAGE = 100
# Pages of the release list read at most (PER_PAGE releases each), so a broken
# "next" link cannot loop for ever.
MAX_PAGES = 50


class ApiError(Exception):
    """A request that failed after every try. `status` is the HTTP status, or None."""

    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def repo_path(path=""):
    """The API path of this repository, such as /repos/<owner>/<name>/releases."""
    return f"/repos/{REPOSITORY}{path}"


def _token():
    return os.environ.get("GITHUB_TOKEN", "").strip()


def _wait_s(headers, attempt, now=None):
    """Seconds to wait before the next try, from Retry-After or X-RateLimit-Reset."""
    now = time.time() if now is None else now
    retry_after = headers.get("Retry-After", "")
    if retry_after.isdigit():
        return int(retry_after)
    if (
        headers.get("X-RateLimit-Remaining") == "0"
        and headers.get("X-RateLimit-Reset", "").isdigit()
    ):
        return max(0, int(headers["X-RateLimit-Reset"]) - int(now)) + 1
    return 2**attempt


def _rate_limited(status, headers):
    return status == 429 or (
        status == 403 and (headers.get("X-RateLimit-Remaining") == "0" or "Retry-After" in headers)
    )


def request(
    method, url, body=None, accept="application/vnd.github+json", opener=None, sleep=time.sleep
):
    """Send one request and return (status, headers, parsed JSON or None).

    `url` is a path such as /repos/... or a full https://api.github.com/ address
    (a "next" link). Retries on rate limits and server errors; raises ApiError for
    any other failure, and for a 404 too (callers that expect one catch it).
    """
    if url.startswith("/"):
        url = API + url
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or parts.hostname != API_HOST:
        raise ApiError(f"refusing to send a request outside {API_HOST}")
    headers = {
        "Accept": accept,
        "User-Agent": f"{REPOSITORY} build",
        "X-GitHub-Api-Version": API_VERSION,
    }
    token = _token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    open_url = opener or urllib.request.urlopen
    where = f"{method} {parts.path}"
    for attempt in range(ATTEMPTS):
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with open_url(req, timeout=TIMEOUT_S) as resp:
                raw = resp.read()
                status, got = resp.status, dict(resp.headers)
        except urllib.error.HTTPError as e:
            status, got = e.code, dict(e.headers or {})
            if attempt + 1 < ATTEMPTS and (_rate_limited(status, got) or status >= 500):
                wait = _wait_s(got, attempt)
                if wait > MAX_WAIT_S:
                    raise ApiError(f"{where}: rate limited for {wait} s", status) from None
                print(f"{where}: HTTP {status}, trying again in {wait} s", file=sys.stderr)
                sleep(wait)
                continue
            raise ApiError(f"{where}: HTTP {status}", status) from None
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt + 1 < ATTEMPTS:
                wait = 2**attempt
                print(f"{where}: {type(e).__name__}, trying again in {wait} s", file=sys.stderr)
                sleep(wait)
                continue
            raise ApiError(f"{where}: {type(e).__name__}") from None
        if not raw:
            return status, got, None
        try:
            return status, got, json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ApiError(f"{where}: the response is not JSON", status) from None
    raise ApiError(f"{where}: no response")  # not reached: the loop returns or raises


def _next_link(headers):
    """The rel="next" address of a Link header, or None."""
    for part in headers.get("Link", "").split(","):
        bits = [b.strip() for b in part.split(";")]
        if (
            len(bits) >= 2
            and 'rel="next"' in bits[1:]
            and bits[0].startswith("<")
            and bits[0].endswith(">")
        ):
            return bits[0][1:-1]
    return None


def get_all(path, accept="application/vnd.github+json", opener=None, sleep=time.sleep):
    """Every item of a paginated list. Raises ApiError when a page is not a list."""
    sep = "&" if "?" in path else "?"
    url = f"{path}{sep}per_page={PER_PAGE}"
    items = []
    for _ in range(MAX_PAGES):
        _, headers, data = request("GET", url, accept=accept, opener=opener, sleep=sleep)
        if not isinstance(data, list):
            raise ApiError(f"GET {path}: expected a list")
        items.extend(data)
        url = _next_link(headers)
        if not url:
            return items
    raise ApiError(f"GET {path}: more than {MAX_PAGES} pages")
