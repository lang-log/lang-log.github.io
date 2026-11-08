# Progressive web app

Lang Log is a progressive web app (PWA) (the owner's decision, 2026-11-08; `CLAUDE.md`). Here:

## What it has

- `dist/manifest.webmanifest`: written at build time by `tools/pwa.py` (not committed). The name and short name come from `HOME_TITLE` and `SITE_NAME` in `tools/site_brand.py`; the icons are the favicon (`dist/favicon.svg`, any size) and `dist/apple-touch-icon.png` (its size read from the file). All addresses in it are relative, so it works in pull request previews too. No `theme_color` or `background_color`: colours live only in the tokens of `dist/style.css`.
- `dist/sw.js`: the service worker. It stores the top page when installed, and then every page and file of the site the visitor opens, so those open again offline. Pages, data and other files come from the network first; files with `?v=<hash>` (`tools/version_assets.py`) come from the stored copy first. It handles only requests to the site inside its own scope, never other sites (`huggingface.co`) or `/preview/` under the live site, and keeps at most `MAX_ENTRIES` responses. Change `CACHE_VERSION` when the way files are stored changes.
- `dist/pwa.js`: registers `sw.js` from its own address (so a preview registers the preview's worker) with `updateViaCache: 'none'`.
- Nothing is downloaded in advance beyond the top page: the full site is about 500 MB. A page the visitor never opened shows the browser's own offline error; no offline page or text of Lang Log's own.

## Every page

- Every page links the manifest and loads `pwa.js` in `<head>`, with `head_tags()` in `tools/pwa.py`: the generators call it, and the hand-written pages in `dist/*.html` carry the same text (`dist/404.html` from the root, `/`). A new page or generator does the same.
- `tools/build_site.sh` runs `python3 tools/pwa.py --check`, which fails if a page lacks either tag or a file above is missing.
- The Content-Security-Policy allows `manifest-src 'self'` and `worker-src 'self'` (`tools/security_policy.py`).
