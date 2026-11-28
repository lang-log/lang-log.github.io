"""The atlas host (dist/components/tree/): the outline and the zoomable tree that
dist/components/tree/tree.js fills, with its toolbar and Download menu. Its parts carry
classes, not ids, so a page may hold more than one."""

from html import escape

from components.download_menu import download_menu


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
            '<div class="seg" role="group" aria-label="View"><button class="tree-list-button" type="button" aria-pressed="true">List</button>'
            '<button class="tree-chart-button" type="button" aria-pressed="false">Tree</button></div><button class="tree-collapse" type="button">Collapse all</button>'
        )
    )
    outline = (
        ""
        if whole
        else '<div class="tree-outline" role="group" aria-label="Expandable classification outline"></div>'
    )
    # The top page shows only the Download menu, with no box.
    return (
        f'<div class="atlas workspace atlas-embed{" atlas-whole" if whole else ""}"{attrs} hidden>'
        f'<div class="toolbar">{switch}'
        + download_menu(
            f'<button class="tree-export" type="button">SVG (current view)</button>{downloads}'
        )
        + "</div>"
        f"{outline}"
        f'<div class="tree-viewport"{"" if whole else " hidden"}><canvas class="tree-canvas" aria-label="Interactive language classification tree. Click a node to open its page."></canvas>'
        '<div class="canvas-title"><span class="eyebrow">INTEGRATED · SOURCE-CONDITIONED</span><h2 class="tree-title">Language families</h2>'
        '<p class="tree-count">Loading records…</p></div><div class="tree-tooltip" hidden></div>'
        '<div class="zoom"><button class="tree-minus" type="button" aria-label="Zoom out">−</button><button class="tree-fit" type="button">Fit</button>'
        '<button class="tree-plus" type="button" aria-label="Zoom in">+</button></div>'
        "</div></div>"
    )
