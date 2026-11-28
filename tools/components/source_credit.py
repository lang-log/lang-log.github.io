"""The source credit at the foot of the record pages (footer.credit,
dist/components/source-credit/): one source per line, then the contact line."""

from site_brand import contact_line

NEW_TAB = 'target="_blank" rel="noopener noreferrer"'


def credit_line(what, name, url, license_name=None, license_url=None, cite=""):
    """One line of the credit: what the data is, its source, and the license it is used under.
    The citation sits in its own span, so ", used under" stays a text node
    dist/components/language-menu/language-menu.js knows."""
    line = f'<li>{what} <a href="{url}" {NEW_TAB}>{name}</a>'
    if cite:
        # A citation is data in English: kept left to right inside right-to-left pages.
        line += f' <span class="cite" dir="ltr">({cite})</span>'
    if license_name:
        line += f', used under <a href="{license_url}" {NEW_TAB}>{license_name}</a>'
    return line + "</li>"


def source_credit(lines):
    """The credit: `lines` are credit_line()s, in order."""
    return (
        f'<footer class="credit"><ul class="credit-list">{lines}</ul>{contact_line("p")}</footer>'
    )
