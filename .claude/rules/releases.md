# Releases

The owner's decisions (2026-11-08) on how Lang Log is released. Architecture and troubleshooting: "Releases" in `README.md`.

- A release is a Git tag. The owner chooses the commit (on `main`) and the version, and pushes an annotated tag: `git tag -a v1.2.0 -m "..."`, then `git push origin v1.2.0`. CI never picks a version.
- Versions follow Semantic Versioning: `v1.0.0` the first release, `v1.1.0` new features, `v1.1.1` bug fixes, `v2.0.0` breaking changes. Only `vMAJOR.MINOR.PATCH` is accepted (`VERSION_TAG` in `tools/release.py`).
- `.github/workflows/release.yml` (tags `v*`) runs `tools/release.py`: it checks the tag, then creates the GitHub Release named after the tag, with the tag's message followed by GitHub's generated notes. A tag that already has a release is left as it is; never edit or delete past releases or tags from CI.
- GitHub Releases are the one record of releases. The site shows them on `/releases.html` (and `/releases.json`), built by `tools/build_releases.py` from the GitHub API on every build; neither file is committed, and no AI writes or edits release information.
- The site is deployed only by `pages.yml`, after the code checks. It runs when `release.yml` ends; its `releases` job reads the API with `contents: read` and hands the answer to the build as an artifact. Only `release.yml` has `contents: write`.
- Release notes, names and asset names are untrusted: `sanitize()` in `tools/build_releases.py` keeps only plain formatting tags and `https://github.com/` links, and `tools/test_releases.py` (run by `tools/build_site.sh`) covers injected HTML and scripts. Never show the notes unsanitized, never run or open release assets in CI, and never print the token.
- Interface text on the Releases page follows `interface-text.md` (every dictionary); the notes themselves are data and are not translated.
