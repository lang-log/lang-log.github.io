---
paths:
  - ".github/**"
  - "tools/build_site.sh"
---

# Pull request previews

The shared rule is `pr-previews.md` in the `research-aide` repository. Here:

- `tools/build_site.sh` builds and checks `dist/`; both `site.yml` (pull requests) and `pages.yml` (the live site, through the shared workflow) run it. Add a new build or check step there, not in a workflow. The one exception is the code quality checks (Prettier, ESLint, Ruff), which need npm and pip packages: `quality.yml`, run before the build by `site.yml` and before deployment by `pages.yml` (see `code-quality.md`).
- Previews are on Cloudflare Pages, project `lang-log-preview`, at `https://pr-<number>.lang-log-preview.pages.dev/` (`previews.yml`, through the shared workflow). `pages.yml` deploys only the live site (`previews: false`).
- There is no beta site (the owner's decision, 2026-11-28, replacing the `beta` branch of 2026-11-23): only pull request previews and the live site.
- The full site has far more files than the Cloudflare free plan allows in one deployment (20,000), so the preview (`site.yml`) holds every top-level page and data file, `map/`, `data/` and the record pages of `afro-asiatic/` only, not the other families or the source-only pages such as `wals/`. Record links into other families do not open in a preview. If the site grows, keep the preview under that limit; the upload fails above it. `tools/make_preview.sh` is the one place that chooses these files.
- Every pull request from this repository gets one comment that lists the groups of checks as they end (the owner's request, 2026-11-28): `1. Code checks` (`quality.yml`), `2. Build and content checks` (the build and HTML steps of `site.yml`), `3. Browser checks` (the map view and ZIP steps of `site.yml`, and `browsers.yml`), `4. Publishing the preview` (the preview steps of `site.yml` and the preview comment). These are groups A to D of the owner's five; E (watching the live site) runs on a schedule, not on pull requests. `progress.yml` runs `tools/ci_progress.py`, which reads the job and step names of `site.yml` through the API; `tools/test_ci_progress.py` fails when a step it reads is renamed. A new check step goes in one of the groups there.
- The README's `pages` badge shows the state of the latest deployment to the `github-pages` environment (shields.io `github/deployments`), not the latest run of `pages.yml` (the owner's decision, 2026-11-23): many `pages.yml` runs end as skipped or replaced by design, and a workflow badge shows those as failing.
