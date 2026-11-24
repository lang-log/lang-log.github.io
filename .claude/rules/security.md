# Security

The shared rule is `web-security.md` in the `research-aide` repository (security first: every policy the host allows, the strictest setting that keeps the site working). Here:

## What every page carries

- `tools/security_policy.py` holds the one policy, as `<meta>` tags right after `<meta charset="utf-8">`: a Content-Security-Policy (`default-src 'none'`, scripts and images only from the site, styles from the site plus `'unsafe-inline'`, connections only to the site and `https://huggingface.co` for `dist/hf-models.js`, the web app manifest and the service worker only from the site (`manifest-src 'self'`, `worker-src 'self'`, see `pwa.md`), `base-uri 'none'`, `form-action 'self'` for the top-page search form, `object-src 'none'`; no `upgrade-insecure-requests`, see the comment in the file) and `<meta name="referrer" content="same-origin">` (`REFERRER`; the owner's choice, 2026-11-23: requests inside the site carry the full address, other sites get nothing).
- `tools/build_home.py`, `tools/build_paths.py` and `tools/info_page.py` write it from there. The hand-written pages (`dist/404.html`, `dist/q.html`, `dist/record.html`, `dist/signs-and-scripts.html`) carry the same text: after changing the policy, run `python3 tools/security_policy.py --write`.
- `tools/build_site.sh` runs `python3 tools/security_policy.py --check`, which fails if a page lacks the current policy, or has an inline script, an event handler (`onclick=`), a `style="..."` attribute or a `<base>` element.
- `style-src` allows `'unsafe-inline'` (the owner's choice, 2026-11-07): WebKit (Safari) reports a blocked inline stylesheet for every `<select>` under a strict `style-src`, from its own rendering of the menu, which fails the browser check. The alternative was replacing every `<select>` with a custom control. Remove it if WebKit stops doing this or the selects go.
- No `style="..."` attributes all the same, in pages or in HTML built by scripts: use a class in `dist/style.css`. Setting `element.style.x` from a script is allowed by the policy.
- A new outside source (script, style, image, font, API) changes `CSP` in `tools/security_policy.py` in the same pull request.
- Every link that opens a new tab has `rel="noopener noreferrer"`.
- `dist/404.html` is served at any depth, so it uses root-relative links (`/style.css`) instead of `<base>`.

## Response headers (Cloudflare in front of GitHub Pages)

The owner's choice (2026-11-24): `lang-log.com` goes through the Cloudflare proxy, so the live site gets the headers GitHub Pages cannot send.

- The headers are written once, as `LIVE_HEADERS` in `tools/security_policy.py`: the page policy as a header with `frame-ancestors 'none'` (ignored in `<meta>`), `X-Frame-Options: DENY`, `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`, `X-Content-Type-Options: nosniff`, `Referrer-Policy` (`REFERRER`), `Permissions-Policy` turning off every feature the site does not use, and `Cross-Origin-Opener-Policy` / `Cross-Origin-Resource-Policy: same-origin`.
- Cloudflare adds them with one Response Header Transform Rule ("Set static", every request) that the owner keeps; `python3 tools/security_policy.py --live` prints the names and values to enter. Change `LIVE_HEADERS` and the rule together.
- `.github/workflows/headers.yml` (weekly, and by hand) runs `--check-live https://lang-log.com/` and fails when the site sends anything else.
- The beta site on Cloudflare Pages sends the same headers plus `X-Robots-Tag: noindex` (`HEADERS`, written as `_headers`, see `previews.md`).
- Cloudflare settings that would inject scripts into the pages and break the policy stay off: Email Address Obfuscation, Rocket Loader, automatic Web Analytics. "Block AI bots" stays off (the pages are meant to be read by AI assistants too).

Not yet:

- CSP reporting (`report-to`): needs an endpoint to receive the reports.
- Trusted Types (`require-trusted-types-for 'script'`) needs every `innerHTML` write in `dist/*.js` rewritten first; it is Chromium-only for now.

## The certificate behind the Cloudflare proxy

GitHub Pages renews the Let's Encrypt certificate for `lang-log.com`, and renewal is reported to fail sometimes while Cloudflare proxies the domain; with SSL "Full (strict)" an expired GitHub certificate takes the site down. The owner's choice (2026-11-24): fix it automatically and email every step.

- `.github/workflows/certificate.yml` runs `tools/certificate_renewal.py` every day. It reads the custom domain from the Pages settings, checks GitHub's certificate straight at GitHub Pages, and under 21 days left turns the proxy off for the site's A, AAAA and CNAME records (marked by a record comment), waits up to an hour for the new certificate, then turns the proxy back on for the marked records only. Records the owner left "DNS only" are never proxied by it.
- Each step goes to the owner by email at once through one issue, `Certificate renewal for <domain>`, assigned to `NOTIFY_LOGIN` in the workflow: opened when renewal is stuck, commented and closed when it worked, commented with the GitHub and Cloudflare screens and the steps when it did not. The texts are the owner's, in the secrets `CERT_MAIL_DETECTED`, `CERT_MAIL_RENEWED` and `CERT_MAIL_FAILED` of the `dns` environment (the owner's choice, 2026-11-24), with the placeholders listed in `message()`; there is no default text, and a stuck run checks all three before it changes anything.
- The Cloudflare token (`CLOUDFLARE_DNS_TOKEN`, only "Zone / DNS / Edit" for `lang-log.com`) and `CLOUDFLARE_ZONE_ID` live in the `dns` environment, which only the default branch may use. Never give that token to another workflow, and never reuse the Pages token (`CLOUDFLARE_API_TOKEN`) for it.
- Before the token is set up, the check only reads the certificate, and fails only if renewal is stuck.
