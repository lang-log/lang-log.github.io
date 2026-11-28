"""The guide row of the top page (dist/components/guide-row/)."""

from html import escape


def guide_row(links):
    """The row of links under the Random row: `links` are (address, label) pairs."""
    links = "".join(f'<a href="{escape(h)}">{escape(t)}</a>' for h, t in links)
    return f'<nav class="home-guide" aria-label="About Lang Log">{links}</nav>'
