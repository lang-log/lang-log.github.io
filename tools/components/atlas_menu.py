"""The menu of the three atlases (dist/components/atlas-menu/)."""

from html import escape


# Links to the three atlases. No generated page shows them any more (owner, 2026-11-07:
# Lang Log is one tree, not three domains); kept so the UI can be reused.
def domain_nav(up, current="language"):
    items = [
        ("language", up, "Language families"),
        ("sign", f"{up}signs-and-scripts.html?domain=sign", "Sign languages"),
        ("scripts", f"{up}signs-and-scripts.html?domain=scripts", "Writing systems"),
    ]
    return (
        '<nav class="domain-nav" aria-label="Atlas domains">'
        + "".join(
            f'<a href="{escape(h)}"'
            + (' aria-current="page"' if k == current else "")
            + f">{t}</a>"
            for k, h, t in items
        )
        + "</nav>"
    )
