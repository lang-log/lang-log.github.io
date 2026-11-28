"""The list view's button (dist/components/list-view/): the list fills the window, at
#list-view, as the map does at #map-view (owner, 2026-11-28). Its symbols are the map's
Map view button's (ICON_OPEN, ICON_CLOSE in dist/components/map/map.js); the script shows
the one that fits and swaps the label."""

from components.download_menu import map_icon


def list_view_button():
    """The button, hidden until dist/components/list-view/list-view.js shows it (it works only
    with scripts)."""
    return (
        '<button type="button" class="list-view-btn" aria-label="List view" title="List view" '
        'aria-expanded="false" hidden>'
        + map_icon("ICON_OPEN", "list-view-open")
        + map_icon("ICON_CLOSE", "list-view-close")
        + "</button>"
    )
