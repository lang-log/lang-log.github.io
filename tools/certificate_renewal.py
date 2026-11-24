"""Keep GitHub's HTTPS certificate for the custom domain renewing behind the Cloudflare proxy.

GitHub Pages gets the site's certificate from Let's Encrypt and renews it before it
expires. Renewal is reported to fail sometimes while Cloudflare proxies the domain,
and once GitHub's certificate expires, Cloudflare's "Full (strict)" mode refuses it
and the site stops opening. Run daily by .github/workflows/certificate.yml (the
owner's choice, 2026-11-24: fully automatic):

1. Read the custom domain from the GitHub Pages settings (nothing to do without one).
2. Connect straight to GitHub Pages (GITHUB_PAGES_IPS, never through Cloudflare) and
   read how many days GitHub's certificate for that domain has left.
3. Under RENEW_BELOW_DAYS, turn the Cloudflare proxy off for the site's A, AAAA and
   CNAME records (marking them with MARKER), so GitHub can renew, and wait for the new
   certificate. Once it is there, turn the proxy back on for the marked records only.
4. If the new certificate does not come within RENEWAL_WAIT_S, leave the records
   unproxied (the site keeps working, straight from GitHub) and fail. The next run
   puts the proxy back once renewal succeeds.

Every step is sent to the owner by email at once, through one GitHub issue
("Certificate renewal for <domain>", assigned to NOTIFY_LOGIN; the owner's choice,
2026-11-24): opened when renewal is found stuck, a comment and closed when it
worked, a comment with the screens and steps to fix it by hand when it did not.
The texts are the owner's, kept in GitHub Secrets (MESSAGE_SECRETS).

Records the owner left unproxied are never touched: only records this script marked
are proxied again. Needs CLOUDFLARE_DNS_TOKEN (a token with only "Zone / DNS / Edit"
for this zone) and CLOUDFLARE_ZONE_ID; the token is only sent to CLOUDFLARE_API_HOST
and is never printed.
"""

import datetime
import json
import os
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import github_api
from site_brand import REPOSITORY_URL

# GitHub Pages' IPv4 addresses for custom domains (GitHub Docs, "Managing a custom
# domain for your GitHub Pages site"); the site's A records point here.
GITHUB_PAGES_IPS = ("185.199.108.153", "185.199.109.153", "185.199.110.153", "185.199.111.153")
HTTPS_PORT = 443
# Days left on GitHub's certificate under which renewal counts as stuck. Let's
# Encrypt certificates last 90 days and GitHub renews well before the last 30.
RENEW_BELOW_DAYS = 21
# How long one run waits for GitHub to renew, and how often it looks, in seconds.
RENEWAL_WAIT_S = 3600
RENEWAL_POLL_S = 300
# Seconds to wait for one connection or API response.
CONNECT_TIMEOUT_S = 30
SECONDS_PER_DAY = 86400
# The record types that send visitors to the site.
SITE_RECORD_TYPES = ("A", "AAAA", "CNAME")
# Written as the comment of each record whose proxy this script turned off.
MARKER = "auto: proxy off for GitHub certificate renewal"
CLOUDFLARE_API_HOST = "api.cloudflare.com"
CLOUDFLARE_API = f"https://{CLOUDFLARE_API_HOST}/client/v4"
# Where the owner fixes a stuck renewal by hand (named in the failure comment).
PAGES_SETTINGS_URL = f"{REPOSITORY_URL}/settings/pages"
CLOUDFLARE_DNS_URL = "https://dash.cloudflare.com/?to=/:account/:zone/dns/records"
# Records per page of the DNS list (the API's maximum).
CLOUDFLARE_PER_PAGE = 5000


def custom_domain():
    """The custom domain in the repository's GitHub Pages settings, or None."""
    _, _, data = github_api.request("GET", github_api.repo_path("/pages"))
    cname = data.get("cname") if isinstance(data, dict) else None
    return cname if isinstance(cname, str) and cname else None


def days_left(host, ip, now=None):
    """Days until the certificate GitHub serves for `host` at `ip` expires.

    None when it does not verify (expired, or not issued for `host`): renewal is
    needed then too.
    """
    now = time.time() if now is None else now
    context = ssl.create_default_context()
    try:
        with socket.create_connection((ip, HTTPS_PORT), timeout=CONNECT_TIMEOUT_S) as sock:
            with context.wrap_socket(sock, server_hostname=host) as tls:
                cert = tls.getpeercert()
    except ssl.SSLCertVerificationError as e:
        print(f"{ip}: the certificate for {host} does not verify ({e.verify_message})")
        return None
    expires = ssl.cert_time_to_seconds(cert["notAfter"])
    return (expires - now) / SECONDS_PER_DAY


def fewest_days_left(host):
    """The fewest days left over every GitHub Pages address (None if one fails to verify)."""
    days = [days_left(host, ip) for ip in GITHUB_PAGES_IPS]
    return None if None in days else min(days)


def site_records(records, host):
    """The records that send visitors to `host` and `www.<host>`."""
    names = {host, f"www.{host}"}
    return [r for r in records if r.get("name") in names and r.get("type") in SITE_RECORD_TYPES]


def plan(days, records, host):
    """What to change: a list of (record id, proxied, comment).

    Renewal stuck (days is None or under RENEW_BELOW_DAYS): turn the proxy off on
    every proxied site record and mark it. Otherwise: turn it back on for the
    marked records only.
    """
    mine = site_records(records, host)
    if days is None or days < RENEW_BELOW_DAYS:
        return [(r["id"], False, MARKER) for r in mine if r.get("proxied")]
    return [
        (r["id"], True, "") for r in mine if r.get("comment") == MARKER and not r.get("proxied")
    ]


def cloudflare_ready():
    """Whether the Cloudflare token and zone are set (a run before setup only checks)."""
    names = ("CLOUDFLARE_DNS_TOKEN", "CLOUDFLARE_ZONE_ID")
    return all(os.environ.get(n, "").strip() for n in names)


def cloudflare(method, path, body=None):
    """One Cloudflare API request; returns its `result`. Raises RuntimeError on failure."""
    token = os.environ.get("CLOUDFLARE_DNS_TOKEN", "").strip()
    zone = os.environ.get("CLOUDFLARE_ZONE_ID", "").strip()
    if not token or not zone:
        raise RuntimeError("CLOUDFLARE_DNS_TOKEN and CLOUDFLARE_ZONE_ID are needed")
    url = f"{CLOUDFLARE_API}/zones/{urllib.parse.quote(zone, safe='')}{path}"
    if urllib.parse.urlsplit(url).hostname != CLOUDFLARE_API_HOST:
        raise RuntimeError(f"refusing to send a request outside {CLOUDFLARE_API_HOST}")
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    where = f"{method} {path.split('?')[0]}"
    try:
        with urllib.request.urlopen(req, timeout=CONNECT_TIMEOUT_S) as resp:
            answer = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Cloudflare {where}: HTTP {e.code}") from None
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise RuntimeError(f"Cloudflare {where}: {type(e).__name__}") from None
    if not isinstance(answer, dict) or not answer.get("success"):
        raise RuntimeError(f"Cloudflare {where}: not successful")
    return answer.get("result")


def apply(changes):
    for record_id, proxied, comment in changes:
        cloudflare(
            "PATCH",
            f"/dns_records/{urllib.parse.quote(record_id, safe='')}",
            {"proxied": proxied, "comment": comment},
        )
        print(f"record {record_id}: proxy {'on' if proxied else 'off'}")


def dns_records():
    result = cloudflare("GET", f"/dns_records?per_page={CLOUDFLARE_PER_PAGE}")
    if not isinstance(result, list):
        raise RuntimeError("Cloudflare GET /dns_records: expected a list")
    return result


def describe(days):
    return "does not verify" if days is None else f"{days:.1f} days left"


def run_url():
    parts = [
        os.environ.get(k, "") for k in ("GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "GITHUB_RUN_ID")
    ]
    return (
        f"{parts[0]}/{parts[1]}/actions/runs/{parts[2]}"
        if all(parts)
        else "(not in GitHub Actions)"
    )


def issue_title(host):
    return f"Certificate renewal for {host}"


def open_issue(host):
    """The number of the open renewal issue, or None."""
    issues = github_api.get_all(github_api.repo_path("/issues?state=open"))
    for issue in issues:
        if issue.get("title") == issue_title(host) and "pull_request" not in issue:
            return issue.get("number")
    return None


# The owner keeps the email texts in GitHub Secrets (the owner's choice, 2026-11-24), in the
# "dns" environment: one secret per step, each a text with the placeholders of message().
MESSAGE_SECRETS = {
    "detected": "CERT_MAIL_DETECTED",
    "renewed": "CERT_MAIL_RENEWED",
    "failed": "CERT_MAIL_FAILED",
}


def message(step, host, days, records=0):
    """The text for one step, from its secret, with {host}, {days}, {records}, {wait_minutes},
    {threshold_days}, {pages_url}, {cloudflare_url} and {run} filled in.

    Fails when the secret is missing or names another placeholder: there is no default text.
    """
    name = MESSAGE_SECRETS[step]
    template = os.environ.get(name, "")
    if not template.strip():
        raise RuntimeError(f"the secret {name} is not set")
    values = {
        "host": host,
        "days": describe(days),
        "records": records,
        "wait_minutes": RENEWAL_WAIT_S // 60,
        "threshold_days": RENEW_BELOW_DAYS,
        "pages_url": PAGES_SETTINGS_URL,
        "cloudflare_url": CLOUDFLARE_DNS_URL,
        "run": run_url(),
    }
    try:
        return template.format_map(values)
    except (KeyError, IndexError, ValueError) as e:
        raise RuntimeError(
            f"the secret {name} has a placeholder this check does not fill: {e}"
        ) from None


def notify_detected(host, days, changes):
    """Open the renewal issue, assigned to NOTIFY_LOGIN, so the owner gets an email at once."""
    body = message("detected", host, days, len(changes))
    number = open_issue(host)
    if number is not None:
        _comment(number, body)
        return number
    issue = {"title": issue_title(host), "body": body}
    login = os.environ.get("NOTIFY_LOGIN", "").strip()
    if login:
        issue["assignees"] = [login]
    _, _, data = github_api.request("POST", github_api.repo_path("/issues"), issue)
    return data.get("number") if isinstance(data, dict) else None


def notify_renewed(host, days, number):
    """Say on the issue that renewal worked, and close it."""
    if number is None:
        return
    _comment(number, message("renewed", host, days))
    github_api.request("PATCH", github_api.repo_path(f"/issues/{number}"), {"state": "closed"})


def notify_failed(host, days, number):
    """Say on the issue that renewal did not come, with the screens and steps to fix it."""
    if number is None:
        return
    _comment(number, message("failed", host, days))


def _comment(number, body):
    github_api.request("POST", github_api.repo_path(f"/issues/{number}/comments"), {"body": body})


def main():
    host = custom_domain()
    if not host:
        print("No custom domain in the GitHub Pages settings; nothing to check.")
        return 0
    days = fewest_days_left(host)
    print(f"GitHub's certificate for {host}: {describe(days)}")
    if not cloudflare_ready():
        if days is not None and days >= RENEW_BELOW_DAYS:
            print("Cloudflare is not set up for this check yet; nothing to change.")
            return 0
        raise RuntimeError("renewal is stuck and CLOUDFLARE_DNS_TOKEN is not set up")
    if days is None or days < RENEW_BELOW_DAYS:
        # Every email text must work before anything changes in Cloudflare.
        for step in MESSAGE_SECRETS:
            message(step, host, days)
    changes = plan(days, dns_records(), host)
    apply(changes)
    if days is not None and days >= RENEW_BELOW_DAYS:
        notify_renewed(host, days, open_issue(host))
        return 0
    number = notify_detected(host, days, changes)
    deadline = time.time() + RENEWAL_WAIT_S
    while time.time() < deadline:
        time.sleep(RENEWAL_POLL_S)
        days = fewest_days_left(host)
        print(f"{datetime.datetime.now(datetime.UTC):%H:%M} UTC: {describe(days)}")
        if days is not None and days >= RENEW_BELOW_DAYS:
            apply(plan(days, dns_records(), host))
            notify_renewed(host, days, number)
            print("Renewed; the proxy is back on.")
            return 0
    notify_failed(host, days, number)
    print(f"GitHub did not renew the certificate for {host}; see the issue.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
