"""Check the interface text in i18n/*.yaml and write the dictionaries the pages load.

i18n/en.yaml holds every piece of interface text in English, under a key; each
other interface language has i18n/<code>.yaml with the same keys (the languages
are LANGS in dist/lang.js). This script fails when a language lacks a key, has
a key en.yaml does not, has an empty text, or uses a placeholder its English
text does not have.

It writes (not committed; run by tools/build_site.sh):
  dist/i18n.js         the Japanese dictionary, loaded by every page
  dist/i18n/<code>.js  every other language, loaded by dist/lang.js when chosen

The pages are written in English and dist/lang.js translates their text with
these dictionaries. Each maps English text to its translation:
  exact     text without placeholders: {English: translation}
  patterns  text with placeholders: [regular expression, replacement], where
            the expression matches the English text with any value in place of
            each placeholder, $1 in the replacement is the value of the first
            one, and $t1 that value translated.
"""

import json
import re
import sys

import yaml

from locations import DIST, LANG_JS, ROOT

SOURCE = ROOT / "i18n"

PLACEHOLDER = re.compile(r"\{([a-z][a-z0-9]*)(\|tr)?\}")
# What a placeholder matches unless en.yaml's `match` says otherwise: {count},
# {count2} ... are numbers as the scripts write them (1,234), {date} a date as
# dist/lang.js reads it (3 Nov 2026), any other name any text.
NUMBER = r"[\d,]+"
DATE = r"\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{4}"
ANY_TEXT = r".+?"
# Characters with a meaning in a JavaScript regular expression.
REGEX_SPECIAL = re.compile(r"([\\^$.*+?()[\]{}|/])")


def default_match(name):
    if name.startswith("count"):
        return NUMBER
    if name == "date":
        return DATE
    return ANY_TEXT


def languages():
    """The interface languages, from LANGS in dist/lang.js (English first)."""
    table = re.search(r"var LANGS = \[([\s\S]*?)\];", LANG_JS.read_text(encoding="utf-8"))
    if not table:
        sys.exit("dist/lang.js: LANGS table not found")
    return re.findall(r"\['([A-Za-z-]+)'", table.group(1))


def flatten(text, where):
    """{section: {key: text}} -> {"section.key": text}."""
    flat = {}
    if not isinstance(text, dict):
        sys.exit(f"{where}: `text` must be a mapping of sections")
    for section, entries in text.items():
        if not isinstance(entries, dict):
            sys.exit(f"{where}: section {section} must be a mapping of keys")
        for key, value in entries.items():
            flat[f"{section}.{key}"] = value
    return flat


def load(code):
    path = SOURCE / f"{code}.yaml"
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def pattern(english, match):
    """The regular expression (as JavaScript source) for an English text with
    placeholders, and the placeholder names in order."""
    names, parts, last = [], ["^"], 0
    for m in PLACEHOLDER.finditer(english):
        parts.append(REGEX_SPECIAL.sub(r"\\\1", english[last : m.start()]))
        names.append(m.group(1))
        parts.append("(" + match.get(m.group(1), default_match(m.group(1))) + ")")
        last = m.end()
    parts.append(REGEX_SPECIAL.sub(r"\\\1", english[last:]) + "$")
    return "".join(parts), names


def replacement(text, names):
    """A translation with placeholders -> the replacement dist/lang.js applies."""
    return PLACEHOLDER.sub(
        lambda m: "$" + ("t" if m.group(2) else "") + str(names.index(m.group(1)) + 1), text
    )


def main():
    errors = []
    codes = languages()
    en = load("en")
    if en is None:
        sys.exit("i18n/en.yaml is missing")
    english = flatten(en.get("text"), "i18n/en.yaml")
    match = en.get("match") or {}
    for key in match:
        if key not in english:
            errors.append(f"i18n/en.yaml: match for unknown key {key}")
    seen = {}
    for key, text in english.items():
        if not isinstance(text, str) or not text.strip():
            errors.append(f"i18n/en.yaml: empty text {key}")
        elif text in seen:
            errors.append(f"i18n/en.yaml: {key} has the same text as {seen[text]}")
        else:
            seen[text] = key
        if "|tr}" in str(text):
            errors.append(f"i18n/en.yaml: {key}: |tr belongs in translations only")

    files = {p.stem for p in SOURCE.glob("*.yaml")}
    for extra in sorted(files - set(codes)):
        errors.append(f"i18n/{extra}.yaml: not a language in LANGS (dist/lang.js)")

    dictionaries = {}
    for code in codes:
        if code == "en":
            continue
        where = f"i18n/{code}.yaml"
        data = load(code)
        if data is None:
            errors.append(f"{where} is missing")
            continue
        if not isinstance(data.get("join"), str):
            errors.append(f"{where}: join must be a string")
        text = flatten(data.get("text"), where)
        for key in text.keys() - english.keys():
            errors.append(f"{where}: {key} is not in i18n/en.yaml")
        exact, patterns = {}, []
        for key, source in english.items():
            if key not in text:
                errors.append(f"{where}: missing {key}")
                continue
            translated = text[key]
            if not isinstance(translated, str) or not translated.strip():
                errors.append(f"{where}: empty {key}")
                continue
            if not PLACEHOLDER.search(source):
                if PLACEHOLDER.search(translated):
                    errors.append(f"{where}: {key} has a placeholder its English text lacks")
                exact[source] = translated
                continue
            regex, names = pattern(source, match.get(key, {}))
            unknown = [
                m.group(1) for m in PLACEHOLDER.finditer(translated) if m.group(1) not in names
            ]
            if unknown:
                errors.append(f"{where}: {key} uses {unknown}, not in its English text")
                continue
            patterns.append([regex, replacement(translated, names)])
        dictionaries[code] = {"join": data.get("join"), "exact": exact, "patterns": patterns}

    if errors:
        sys.exit("\n".join(errors))

    (DIST / "i18n").mkdir(exist_ok=True)
    for code, dictionary in dictionaries.items():
        body = json.dumps(dictionary, ensure_ascii=False, indent=1)
        script = (
            "// Written by tools/build_i18n.py from i18n/" + code + ".yaml; do not edit.\n"
            "(window.LANGLOG_I18N = window.LANGLOG_I18N || {})["
            + json.dumps(code)
            + "] = "
            + body
            + ";\n"
        )
        out = DIST / "i18n.js" if code == "ja" else DIST / "i18n" / f"{code}.js"
        out.write_text(script, encoding="utf-8")
    print(
        f"i18n: {len(dictionaries)} dictionaries, {len(english)} texts each "
        f"({sum(1 for t in english.values() if PLACEHOLDER.search(t))} with placeholders)"
    )


if __name__ == "__main__":
    main()
