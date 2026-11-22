# Lang Log documentation

The documentation of Lang Log lives here, in the repository, and is reviewed in pull requests like the code (owner, 2026-11-20: no GitHub Wiki; issues #89 and #92). How to build, check and release the site stays in the top-level `README.md`; the rules Claude follows are in `CLAUDE.md` and `.claude/rules/`.

- [`site.md`](site.md): how the pages work: the top page, record pages, maps, logo, interface language and theme, search, Hugging Face models, sign languages and writing systems.
- [`data.md`](data.md): how the data is built from its sources, what each page generator reads, and what the pages load.
- [`urls.md`](urls.md): every address of the site, its data files and every query parameter.
- [`components.md`](components.md): every UI component by name, with its markup, the file that builds it and the file that styles it.

A change that adds a page, a parameter or a component updates the file here in the same pull request.
