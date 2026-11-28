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
- The README's `pages` badge shows the state of the latest deployment to the `github-pages` environment (shields.io `github/deployments`), not the latest run of `pages.yml` (the owner's decision, 2026-11-23): many `pages.yml` runs end as skipped or replaced by design, and a workflow badge shows those as failing.
