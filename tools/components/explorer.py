"""The list / map explorer shared by the top page (tools/build_home.py) and the record
pages (tools/build_paths.py): the conditions the two views share. Both views are shown
together, the map first (owner, 2026-11-28). dist/components/explorer/explorer.js runs it on the element marked `explorer`, which says where the site
root is (data-base) and, on a record page, which languages it narrows (data-langs)."""

from html import escape

from components.conditions_panel import conditions_html


def explore_open(classes, base, total, langs=None, section_id=""):
    """The start of the explorer: its element and the conditions. The views follow, each a
    `.explore-view` with its data-view, the map first."""
    attrs = f' id="{escape(section_id)}"' if section_id else ""
    attrs += f' data-base="{escape(base)}"'
    if langs is not None:
        attrs += f' data-langs="{escape(" ".join(langs))}"'
    return f'<section class="{escape(classes)} explorer"{attrs}>{conditions_html(total)}'
