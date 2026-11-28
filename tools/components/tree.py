"""The atlas host (dist/components/tree/): the outline and the zoomable tree that
dist/components/tree/tree.js fills, with its toolbar and Download menu."""

from html import escape

from components.download_menu import download_menu
from components.list_view import list_view_button


def atlas_html(base, root=None, src=None, downloads=""):
    """The zoomable tree that dist/components/tree/tree.js fills: the branch below a record (record
    pages, with its outline and a List / Tree switch), or every root (the top page's
    list, without them: only its Download menu shows there, and the canvas is drawn
    for the SVG export, dist/components/tree/tree.js)."""
    whole = root is None
    attrs = f' data-base="{escape(base)}"' + (
        "" if whole else f' data-root="{escape(root)}" data-src="{escape(src)}"'
    )
    switch = (
        ""
        if whole
        else (
            '<div class="seg" role="group" aria-label="View"><button id="listview" type="button" aria-pressed="true">List</button>'
            '<button id="chartview" type="button" aria-pressed="false">Tree</button></div><button id="collapse" type="button">Collapse all</button>'
        )
    )
    outline = (
        ""
        if whole
        else '<div id="outline" role="group" aria-label="Expandable classification outline"></div>'
    )
    # The top page shows only the Download menu, with no box.
    return (
        f'<div id="atlas" class="workspace atlas-embed{" atlas-whole" if whole else ""}"{attrs} hidden>'
        f'<div class="toolbar">{switch}'
        + download_menu(f'<button id="export" type="button">SVG (current view)</button>{downloads}')
        + list_view_button()
        + "</div>"
        f"{outline}"
        f'<div id="viewport"{"" if whole else " hidden"}><canvas id="tree" aria-label="Interactive language classification tree. Click a node to open its page."></canvas>'
        '<div class="canvas-title"><span class="eyebrow">INTEGRATED · SOURCE-CONDITIONED</span><h2 id="view-title">Language families</h2>'
        '<p id="view-count">Loading records…</p></div><div id="tooltip" hidden></div>'
        '<div class="zoom"><button id="minus" type="button" aria-label="Zoom out">−</button><button id="fit" type="button">Fit</button>'
        '<button id="plus" type="button" aria-label="Zoom in">+</button></div>'
        "</div></div>"
    )
