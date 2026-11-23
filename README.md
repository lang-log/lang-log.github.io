# Lang Log

[![site](https://github.com/lang-log/lang-log.github.io/actions/workflows/site.yml/badge.svg?branch=main&event=push)](https://github.com/lang-log/lang-log.github.io/actions/workflows/site.yml?query=branch%3Amain)
[![pages](https://img.shields.io/github/deployments/lang-log/lang-log.github.io/github-pages?label=pages)](https://github.com/lang-log/lang-log.github.io/deployments/github-pages)
[![License: all rights reserved](https://img.shields.io/badge/license-all%20rights%20reserved-lightgrey)](LICENSE)
[![Stars](https://img.shields.io/github/stars/lang-log/lang-log.github.io)](https://github.com/lang-log/lang-log.github.io/stargazers)
[![Last commit](https://img.shields.io/github/last-commit/lang-log/lang-log.github.io/main)](https://github.com/lang-log/lang-log.github.io/commits/main)

An interactive atlas of language families, sign languages and writing systems, with source-linked classifications, alternative hypotheses and exportable data.

It will also hold corpora and data for low-resource languages (planned).

Live site: <https://lang-log.com/>

## Run locally

The scripts live in `tools/`; run them from the repository root. Install the one package the build needs with `python3 -m pip install --require-hashes -r requirements.txt`, then run `bash tools/build_site.sh` (it converts `source-data/` into `dist/` and writes every page), then serve the static site with `python -m http.server 8000 --directory dist` and open <http://localhost:8000>.

## Code quality checks

Every pull request and every push to `main` runs Prettier (formatting, with `@prettier/plugin-xml` for XML and SVG; it also fails on JSON, YAML and XML that do not parse), ESLint (JavaScript), markdownlint (Markdown, `.markdownlint-cli2.jsonc`), html-validate (the hand-written pages in `dist/`, `.htmlvalidate.json`), Stylelint (CSS syntax, `.stylelintrc.json`), ShellCheck (shell scripts) and Ruff (Python lint and formatting) before the site is built (`.github/workflows/quality.yml`, called by `site.yml`). `pages.yml` runs the same checks on `main` before every deployment, so nothing is published while they fail. The site itself needs no packages (the build needs PyYAML, `requirements.txt`); these tools are only for development.

Tools: Node.js 22 (`.nvmrc`) with npm, and Python 3.12 or later.

Install the exact versions once, from the repository root:

```sh
npm ci --ignore-scripts
python3 -m pip install --require-hashes -r requirements-dev.txt
```

Run every check:

```sh
npm run check
```

Or one at a time:

| Command                       | What it does                                     |
| ----------------------------- | ------------------------------------------------ |
| `npm run format:check`        | Prettier: lists files that are not formatted     |
| `npm run lint:js`             | ESLint on the JavaScript in `dist/` and `tools/` |
| `npm run lint:md`             | markdownlint on the Markdown files               |
| `npm run lint:html`           | html-validate on the hand-written pages          |
| `npm run lint:css`            | Stylelint on the stylesheets                     |
| `npm run lint:python`         | Ruff lint on the Python in `tools/`              |
| `npm run format:python:check` | Ruff: lists Python files that are not formatted  |
| `npm run format`              | Prettier: formats the files (writes them)        |
| `npm run format:python`       | Ruff: formats the Python files (writes them)     |

`tools/build_site.sh` adds asset versions to `dist/lang.js` and the hand-written pages in `dist/`, so run the checks before building, or restore those files first with `git checkout -- dist`.

Settings: `.prettierrc.json` and `.prettierignore` (Prettier), `eslint.config.mjs` (ESLint), `pyproject.toml` (Ruff). Pinned versions: `package-lock.json` and `requirements-dev.txt`.

Left out on purpose:

- `source-data/`: third-party datasets and saved pages kept as published, and hand-curated data the build reads as it is (Prettier, Ruff).
- Files written by scripts and committed: `dist/hf-iso-map.js`, `dist/logo.svg` and `dist/map/` (Prettier). OPML and CSV files are not formatted by any of the tools.
- Everything in `.gitignore`, such as the pages and data that `tools/build_site.sh` writes into `dist/` (all tools).
- `dist/*.html`: `tools/security_policy.py --write` keeps their policy `<meta>` tags as one exact string after `<meta charset="utf-8">`, and `--check` compares that text (Prettier).

## Documentation

How the site and its data work is in [`docs/`](docs/README.md): the pages, the data, every address and query parameter, and every UI component.

## Badges

The badges at the top show: the `site` workflow (code checks and build) on `main`, the `pages` deployment, the latest GitHub Release (none until the first version tag), the license and the last commit on `main`. Only badges that describe this repository are used; package, download, coverage, sponsor and community badges are left out because Lang Log publishes no package, has no coverage report, and is not open source (`LICENSE`). The images come from GitHub and shields.io and are shown only on GitHub, never on the site.

## License

Lang Log is not open source. Its code, design, site text and the data compiled for it are copyright (C) 2026 MATSUURA Yoshihiro, all rights reserved; see `LICENSE`. No reuse, in whole or in part, commercial or non-commercial, without prior written permission. Versions published earlier under AGPL-3.0-only stay under that license for those who received them.

Third-party source datasets are not covered by this and keep their own licenses and attribution (for example Glottolog: CC BY 4.0; SIL Scripts Index: CC BY-SA 4.0; Power et al. 2020 CLDF dataset: GPL-3.0). See `dist/signs-and-scripts-licenses.txt`, the source registers in the site and [`docs/data.md`](docs/data.md).

## GitHub Pages

The workflow `.github/workflows/pages.yml` publishes `dist/` to <https://lang-log.com/> through the shared workflow `pages-with-previews.yml` of `nguekwang/research-aide`: it builds the default branch with `tools/build_site.sh` (which builds and checks `dist/`). It runs on every push to `main`, after every release (see Releases), and by hand. One-time setup: Settings > Pages > Build and deployment > Source: GitHub Actions, and Custom domain: `lang-log.com` with Enforce HTTPS (`SITE_URL` in `tools/site_brand.py` must match it); GitHub then redirects `lang-log.github.io` to it.

## Pull request previews

`site.yml` builds and checks each pull request and uploads its preview; `.github/workflows/previews.yml` (shared workflow `cloudflare-previews.yml` of `nguekwang/research-aide`) publishes it on Cloudflare Pages at `https://pr-<number>.lang-log-preview.pages.dev/`, links it on the pull request, and deletes it when the pull request is closed. One-time setup: a Cloudflare Pages project `lang-log-preview` made with Direct Upload, and the repository secrets `CLOUDFLARE_API_TOKEN` (a token with only "Account / Cloudflare Pages / Edit") and `CLOUDFLARE_ACCOUNT_ID`. The other workflows need no secrets: they use the `GITHUB_TOKEN` GitHub gives each job, with the permissions set in each workflow.

## Releases

A release is a version tag on a commit of `main`; GitHub Releases hold the release information, and the site shows it on `releases.html`. The rules are in `.claude/rules/releases.md`.

To release, choose the commit and the version (Semantic Versioning: `v1.0.0` first release, `v1.1.0` new features, `v1.1.1` bug fixes, `v2.0.0` breaking changes) and push an annotated tag:

```sh
git switch main && git pull
git tag -a v1.0.0 -m "First public release"
git push origin v1.0.0
```

What happens next:

1. `.github/workflows/release.yml` starts on the tag push (`push`, tags `v*`). Its job has `contents: write` and runs `tools/release.py`, which checks that the tag is `vMAJOR.MINOR.PATCH` and points at a commit on `main` (a lightweight tag only gives a warning), then creates the GitHub Release: named after the tag, with the tag's message followed by the notes GitHub generates from the pull requests merged since the previous release. If the tag already has a release, nothing is changed.
2. When `release.yml` ends, `pages.yml` runs (`workflow_run`). Its `releases` job (`contents: read`) runs `python3 tools/build_releases.py --fetch`, which reads every release and the latest one from the GitHub API with the job's `GITHUB_TOKEN` and saves the answer as `build/github-releases.json`, uploaded as the artifact `github-releases`. After the code checks (`quality.yml`), the shared deployment workflow downloads it and runs `tools/build_site.sh`.
3. `tools/build_site.sh` runs the tests (`tools/test_releases.py`) and `tools/build_releases.py`, which writes `dist/releases.html` (newest first, the latest release marked, notes, links to each release and its downloads on GitHub) and `dist/releases.json` (the same releases with the notes in Markdown). Neither is committed. The page is then deployed with the rest of the site.

`pages.yml` runs one deployment at a time (workflow-level `concurrency`, never cancelled while running); a waiting run reads the releases when it starts, so a deployment that replaced it still shows the newest release. `site.yml` fetches the releases the same way before building a pull request. Without `build/github-releases.json` (a local build, the browser check), `tools/build_releases.py` reads the API itself, anonymously unless `GITHUB_TOKEN` is set.

Security: release notes, names and asset names are untrusted. The page shows GitHub's HTML of the notes after `sanitize()` keeps only plain formatting tags and `https://github.com/` links; images are replaced by their alternative text (the Content-Security-Policy allows only the site's own images). Assets are only linked, never downloaded or run. API requests go only to `api.github.com`, retry on rate limits and server errors (at most `ATTEMPTS` tries, waiting at most `MAX_WAIT_S` seconds, in `tools/github_api.py`), and never print the token.

Troubleshooting:

- No release was created: open the `release` run of the tag. `is not a version tag` means the name is not like `v1.2.0`; `is not on origin/main` means the tagged commit is not on `main`. Delete the tag (`git push origin :refs/tags/v1.2.0`, `git tag -d v1.2.0`) and tag a commit of `main`.
- The release exists but the site does not show it: check the `pages` run that followed. If `releases` failed (API error or rate limit), nothing was deployed and the live site is unchanged; run `pages` again from the Actions tab (workflow_dispatch).
- A local build fails with an HTTP 403: the anonymous rate limit was reached. Wait, or set `GITHUB_TOKEN` to a token that can read the repository.
