"""The Hugging Face models section (dist/components/hf-models/)."""

from html import escape


def hf_html(n):
    """Hugging Face models, loaded from the Hub when the section scrolls into view (dist/record-page.js)."""
    return (
        f'<section class="hf-models" id="hf-models" hidden data-name="{escape(n["name"])}" '
        f'data-level="{escape(n.get("level", ""))}" data-iso="{escape(n.get("iso", ""))}" aria-label="Hugging Face models"></section>'
    )
