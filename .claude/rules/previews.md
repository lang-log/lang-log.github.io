---
paths:
  - ".github/**"
  - "tools/build_site.sh"
---

# Pull request previews

The shared rule is `pr-previews.md` in the `research-aide` repository. Here:

- `tools/build_site.sh` builds and checks `dist/`; both `site.yml` (pull requests) and `pages.yml` (the live site, through the shared workflow) run it. Add a new build or check step there, not in a workflow.
- The full site is about 500 MB and GitHub Pages allows 1 GB, so the preview (`site.yml`) holds every top-level page and data file, `map/`, `data/` and the record pages of `afro-asiatic/` only (about 120 MB), not the other families or the source-only pages such as `wals/`. Record links into other families do not open in a preview. If the site grows, keep the preview under about 130 MB so three previews fit next to the live site.
