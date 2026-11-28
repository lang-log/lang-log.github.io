"""The switch between views (.seg.explore-views, dist/components/view-switch/), used by the
explorer (tools/components/explorer.py)."""

# The views, in the order of the switch: (key, label). dist/components/explorer/explorer.js reads the keys from
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
