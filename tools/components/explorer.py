"""The list / map explorer shared by the top page (tools/build_home.py) and the record
pages (tools/build_paths.py): a switch between the views, and the conditions the views
share. dist/components/explorer/explorer.js runs it on the element marked `explorer`, which says where the site
root is (data-base) and, on a record page, which languages it narrows (data-langs)."""

from html import escape

from components.conditions_panel import conditions_html
from components.view_switch import view_switch


def explore_open(classes, base, current, total, langs=None, section_id=""):
    """The start of the explorer: its element, the switch and the conditions. The views
    follow, each a `.explore-view` with its data-view."""
    attrs = f' id="{escape(section_id)}"' if section_id else ""
    attrs += f' data-base="{escape(base)}"'
    if langs is not None:
        attrs += f' data-langs="{escape(" ".join(langs))}"'
    return f'<section class="{escape(classes)} explorer"{attrs}>{view_switch(current)}{conditions_html(total)}'
