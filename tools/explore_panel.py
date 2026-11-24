"""The list / map explorer shared by the top page (tools/build_home.py) and the record
pages (tools/build_paths.py): a switch between the views, and the conditions the views
share. dist/explore.js runs it on the element marked `explorer`, which says where the site
root is (data-base) and, on a record page, which languages it narrows (data-langs)."""

from html import escape

# The views, in the order of the switch: (key, label). dist/explore.js reads the keys from
# the buttons, and the pressed one is the view shown when the address names none.
VIEWS = [("list", "List"), ("map", "Map")]


def view_switch(current):
    """The switch between the views (.seg.explore-views), with `current` pressed. It works
    only with scripts, so style.css hides it when they are off."""
    buttons = "".join(
        f'<button type="button" data-view="{v}" aria-pressed="{str(v == current).lower()}">{label}</button>'
        for v, label in VIEWS
    )
    return f'<div class="seg explore-views" role="group" aria-label="View">{buttons}</div>'


def conditions_html(total):
    """The conditions panel. It is in the first paint, so nothing moves when the data
    arrives; dist/explore.css hides it when scripts are off. The count line starts with
    every language (`total`), the sentence dist/explore.js apply() writes with no
    conditions."""
    return (
        '<div class="explore-filter wm-legend">'
        f'<p id="count" class="wm-count">Showing {total} of {total} languages</p>'
        '<div class="explore-colour" hidden><label class="wm-colour">Colour by <span id="colour-slot"></span></label>'
        # Sets the Latitude and Longitude conditions to the part of the map in view.
        '<button type="button" id="use-area" class="wm-add">Use the area in view</button></div>'
        '<h3 class="wm-conds-title">Conditions</h3>'
        '<div id="conditions"></div>'
        # Shown by dist/explore.js once there are two conditions; empty = AND / OR as set.
        '<label class="wm-min" hidden>Minimum number of conditions to match '
        '<input type="number" id="min-match" min="1" step="1" inputmode="numeric"></label>'
        '<button type="button" id="add-condition" class="wm-add">+ Add condition</button></div>'
    )


def explore_open(classes, base, current, total, langs=None, section_id=""):
    """The start of the explorer: its element, the switch and the conditions. The views
    follow, each a `.explore-view` with its data-view."""
    attrs = f' id="{escape(section_id)}"' if section_id else ""
    attrs += f' data-base="{escape(base)}"'
    if langs is not None:
        attrs += f' data-langs="{escape(" ".join(langs))}"'
    return f'<section class="{escape(classes)} explorer"{attrs}>{view_switch(current)}{conditions_html(total)}'
