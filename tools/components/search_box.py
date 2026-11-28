"""The search box of the top page (dist/components/search-box/): a plain GET form to the
search results page, so it works without scripts."""

from html import escape


def search_box(action):
    """The form; `action` is the address of the search results page."""
    return (
        f'<form class="home-search" action="{escape(action)}" method="get" role="search">'
        '<label class="visually-hidden" for="home-q">Search languages and families</label>'
        '<div class="search-pill">'
        '<input id="home-q" name="q" type="search" placeholder="Name, ISO code, Glottocode…" autocomplete="off">'
        '<button type="submit" aria-label="Search" title="Search">'
        '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5 21 21"/></svg>'
        "</button></div></form>"
    )
