---
paths:
  - ".github/**"
  - "tools/build_site.sh"
---

# Pull request previews

The shared rule is `pr-previews.md` in the `research-aide` repository. Here:

- `tools/build_site.sh` builds and checks `dist/`; both `site.yml` (pull requests) and `pages.yml` (the live site, through the shared workflow) run it. Add a new build or check step there, not in a workflow. The one exception is the code quality checks (Prettier, ESLint, Ruff), which need npm and pip packages: `quality.yml`, run before the build by `site.yml` and before deployment by `pages.yml` (see `code-quality.md`).
- Previews are on Cloudflare Pages, project `lang-log-preview`, at `https://pr-<number>.lang-log-preview.pages.dev/` (`previews.yml`, through the shared workflow). `pages.yml` deploys only the live site (`previews: false`).
- The full site has far more files than the Cloudflare free plan allows in one deployment (20,000), so the preview (`site.yml`) holds every top-level page and data file, `map/`, `data/` and the record pages of `afro-asiatic/` only, not the other families or the source-only pages such as `wals/`. Record links into other families do not open in a preview. If the site grows, keep the preview under that limit; the upload fails above it. `tools/make_preview.sh` is the one place that chooses these files.
- Every pull request from this repository gets one comment that lists the groups of checks as they end (the owner's request, 2026-11-28): `1. Code checks` (`quality.yml`), `2. Build and content checks` (the build and HTML steps of `site.yml`), `3. Browser checks` (the map view and ZIP steps of `site.yml`, and `browsers.yml`), `4. Publishing the preview` (the preview steps of `site.yml` and the preview comment). These are groups A to D of the owner's five; E (watching the live site) runs on a schedule, not on pull requests. `progress.yml` runs `tools/ci_progress.py`, which reads the job and step names of `site.yml` through the API; `tools/test_ci_progress.py` fails when a step it reads is renamed. A new check step goes in one of the groups there.
- The README's `pages` badge shows the state of the latest deployment to the `github-pages` environment (shields.io `github/deployments`), not the latest run of `pages.yml` (the owner's decision, 2026-11-23): many `pages.yml` runs end as skipped or replaced by design, and a workflow badge shows those as failing.

## Beta site

The owner's decisions (2026-11-23; `/decisions/lang-log-beta.md` in the project files):

- The beta site is the `beta` branch, at `https://lang-log-beta.pages.dev/` (the Cloudflare Pages project `lang-log-beta`, no custom domain). The live site stays on GitHub Pages.
- It holds the same part of the site as a preview (`tools/make_preview.sh`), to stay under the Cloudflare free plan's 20,000 files per deployment; the whole site would need a paid plan.
- Anyone with the address may open it; search engines are kept out with `X-Robots-Tag: noindex`.
- `site.yml` builds and checks every push to `beta` and uploads the artifact `beta` with Cloudflare's `_headers` file (`python3 tools/security_policy.py --headers`). `beta.yml` publishes it as the project's production deployment, only for the latest commit of `beta`, and creates the project on its first run. It uses the same secrets as the previews (`CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`).
