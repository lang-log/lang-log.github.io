---
name: ui-edge-cases
description: Checklist of front-end edge cases (browser zoom, screen width, touch, keyboard, theme, interface language, missing fonts, extreme data, browser engines, slow devices) to go through before a pull request that changes what Lang Log visitors see.
---

# Checking the UI for edge cases

Use this after a change to a page, a component, a style or a page script works in the usual case, and before pushing it. The rules themselves live in `.claude/rules/` and the shared rules of `research-aide`; this skill only lists the cases to try. If a line here and a rule file disagree, the rule file wins: fix this skill in the same pull request.

## Steps

1. Build the site (`bash tools/build_site.sh`) and run the checks CI runs. Read `references/automated.md` to see what they already cover, so you do not check it again by hand.
2. Read the checklists for what the change touches, in full (a change of more than one kind reads each file):
   - layout, size, colour or anything drawn: `references/screen.md`;
   - a control, a script or anything a visitor presses, drags or types: `references/input.md`;
   - any text, font or data shown: `references/text-and-data.md`.
3. Try every line that applies in Chromium, Firefox and WebKit, with the setups in `references/how-to-check.md`. Fix the cause at its source (`ui-design.md`, "Reuse before adding"), never for one page, one language or one browser.
4. In the pull request, list the lines you tried, and the lines you could not try and why (for example, a real Android phone).
5. When the owner finds a case these lists miss, add a line for it to the right file in the pull request that fixes it, with the date and what happened. When the case can be checked by a script, add the check too, and move the line to `references/automated.md`.
