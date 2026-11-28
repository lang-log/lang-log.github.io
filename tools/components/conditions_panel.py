"""The conditions panel of the explorer (dist/components/conditions-panel/), run by
dist/components/explorer/explorer.js."""


def conditions_html(total):
    """The conditions panel. It is in the first paint, so nothing moves when the data
    arrives; dist/components/conditions-panel/conditions-panel.css hides it when scripts are off. The count line starts with
    every language (`total`), the sentence dist/components/explorer/explorer.js apply() writes with no
    conditions."""
    return (
        '<div class="explore-filter wm-legend">'
        f'<p id="count" class="wm-count">Showing {total} of {total} languages</p>'
        '<div class="explore-colour" hidden><label class="wm-colour">Colour by <span id="colour-slot"></span></label>'
        # Sets the Latitude and Longitude conditions to the part of the map in view.
        '<button type="button" id="use-area" class="wm-add">Use the area in view</button></div>'
        '<h3 class="wm-conds-title">Conditions</h3>'
        '<div id="conditions"></div>'
        # Shown by dist/components/explorer/explorer.js once there are two conditions; empty = AND / OR as set.
        '<label class="wm-min" hidden>Minimum number of conditions to match '
        '<input type="number" id="min-match" min="1" step="1" inputmode="numeric"></label>'
        '<button type="button" id="add-condition" class="wm-add">+ Add condition</button></div>'
    )
