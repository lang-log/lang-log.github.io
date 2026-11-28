"""Check the UI components in dist/components/ (tools/components/__init__.py).

--check (run by tools/build_site.sh) fails when
- a component directory holds a stylesheet that STYLES leaves out, or STYLES names one
  that is missing;
- a component directory holds a file not named after it (<name>.css, <name>.js);
- a hand-written page in dist/*.html does not load the stylesheets exactly as
  stylesheets() writes them.
--write rewrites the stylesheet tags of the hand-written pages from stylesheets().
"""

import re
import sys

from components import COMPONENTS, STYLES, stylesheets
from locations import DIST

# style.css, then the component stylesheets that follow it.
TAGS = re.compile(
    r'<link rel="stylesheet" href="(/?)style\.css">'
    r'(?:<link rel="stylesheet" href="/?components/[a-z-]+/[a-z-]+\.css">)*'
)


def pages():
    return sorted(DIST.glob("*.html"))


def problems():
    found = []
    dirs = sorted(p.name for p in COMPONENTS.iterdir() if p.is_dir())
    for name in dirs:
        for f in (COMPONENTS / name).iterdir():
            if f.stem != name or f.suffix not in (".css", ".js"):
                found.append(
                    f"dist/components/{name}/{f.name}: a component holds only {name}.css and {name}.js"
                )
        if (COMPONENTS / name / f"{name}.css").exists() and name not in STYLES:
            found.append(
                f"dist/components/{name}/{name}.css is not in STYLES (tools/components/__init__.py)"
            )
    for name in STYLES:
        if not (COMPONENTS / name / f"{name}.css").exists():
            found.append(f"STYLES names {name}, but dist/components/{name}/{name}.css is missing")
    for page in pages():
        text = page.read_text(encoding="utf-8")
        tags = list(TAGS.finditer(text))
        if len(tags) != 1:
            found.append(
                f"dist/{page.name}: expected one run of stylesheet tags from style.css, found {len(tags)}"
            )
        elif tags[0].group(0) != stylesheets(tags[0].group(1)):
            found.append(
                f"dist/{page.name}: stylesheets differ from stylesheets(); run python3 tools/check_components.py --write"
            )
    return found


def main(argv):
    if argv[1:] == ["--write"]:
        for page in pages():
            text = page.read_text(encoding="utf-8")
            new = TAGS.sub(lambda m: stylesheets(m.group(1)), text)
            if new != text:
                page.write_text(new, encoding="utf-8")
                print(f"rewrote dist/{page.name}")
        return 0
    if argv[1:] != ["--check"]:
        print("usage: python3 tools/check_components.py --check | --write", file=sys.stderr)
        return 2
    found = problems()
    for p in found:
        print(p, file=sys.stderr)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
