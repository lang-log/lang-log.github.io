# Security

The shared rule is `web-security.md` in the `research-aide` repository (security first: every policy the host allows, the strictest setting that keeps the site working). Here:

## What every page carries

- `tools/security_policy.py` holds the one policy, as `<meta>` tags right after `<meta charset="utf-8">`: a Content-Security-Policy (`default-src 'none'`, scripts and images only from the site, styles from the site plus `'unsafe-inline'`, connections only to the site and `https://huggingface.co` for `dist/hf-models.js`, the web app manifest and the service worker only from the site (`manifest-src 'self'`, `worker-src 'self'`, see `pwa.md`), `base-uri 'none'`, `form-action 'self'` for the top-page search form, `object-src 'none'`; no `upgrade-insecure-requests`, see the comment in the file) and `<meta name="referrer" content="no-referrer">`.
- `tools/build_home.py` and `tools/build_paths.py` write it from there. The hand-written pages (`dist/404.html`, `dist/record.html`, `dist/signs-and-scripts.html`) carry the same text: after changing the policy, run `python3 tools/security_policy.py --write`.
- `tools/build_site.sh` runs `python3 tools/security_policy.py --check`, which fails if a page lacks the current policy, or has an inline script, an event handler (`onclick=`), a `style="..."` attribute or a `<base>` element.
- `style-src` allows `'unsafe-inline'` (the owner's choice, 2026-11-07): WebKit (Safari) reports a blocked inline stylesheet for every `<select>` under a strict `style-src`, from its own rendering of the menu, which fails the browser check. The alternative was replacing every `<select>` with a custom control. Remove it if WebKit stops doing this or the selects go.
- No `style="..."` attributes all the same, in pages or in HTML built by scripts: use a class in `dist/style.css`. Setting `element.style.x` from a script is allowed by the policy.
- A new outside source (script, style, image, font, API) changes `CSP` in `tools/security_policy.py` in the same pull request.
- Every link that opens a new tab has `rel="noopener noreferrer"`.
- `dist/404.html` is served at any depth, so it uses root-relative links (`/style.css`) instead of `<base>`.

## What GitHub Pages cannot do (waits for a host that sends headers)

These work only as HTTP response headers, which GitHub Pages does not let a site set. Add them when Lang Log moves to a host with headers (see `/decisions/lang-log-backend.md` in the project files; Cloudflare `_headers` would do):

- `Content-Security-Policy` as a header, with `frame-ancestors 'none'` (browsers ignore `frame-ancestors` in `<meta>`) and a `report-to` endpoint.
- `X-Frame-Options: DENY`.
- `Strict-Transport-Security`. Until then, keep "Enforce HTTPS" on in Settings > Pages (github.io is expected to be on the browsers' HSTS preload list; confirm at hstspreload.org).
- `X-Content-Type-Options: nosniff`.
- `Permissions-Policy` turning off camera, microphone, geolocation and the rest (no `<meta>` form exists).
- `Cross-Origin-Opener-Policy: same-origin`, `Cross-Origin-Resource-Policy: same-origin`.
- Trusted Types (`require-trusted-types-for 'script'`) needs the 28 `innerHTML` writes in `dist/*.js` rewritten first; it is Chromium-only for now.
