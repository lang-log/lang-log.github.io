"""The classification path above a record's name (.lineage, dist/components/breadcrumb/)."""

from html import escape


def breadcrumb(items, label):
    """The path: `items` are (address, name) pairs from the top down; `label` names whose
    classification it follows (only in the aria-label, never shown). Nothing when empty."""
    links = "".join(f'<li><a href="{escape(h)}">{escape(name)}</a></li>' for h, name in items)
    if not links:
        return ""
    return f'<nav class="lineage" aria-label="Classification according to {escape(label)}"><ol class="lineage-path">{links}</ol></nav>'
