"""The page footer (dist/components/footer/): each part on its own line, then the
copyright line and the contact line."""

from site_brand import COPYRIGHT, contact_line


def footer(*parts):
    """`parts` are HTML lines shown before the copyright line."""
    lines = "".join(f"<span>{p}</span>" for p in (*parts, COPYRIGHT))
    return f"<footer>{lines}{contact_line()}</footer>"
