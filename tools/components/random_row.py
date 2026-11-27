"""The Random row of the top page (dist/components/random-row/)."""


def random_row():
    """One Random button. The three buttons per domain (language, sign
    language, writing system) were removed with the three-way split (owner,
    2026-11-07); see the git history to reuse them."""
    button = (
        '<button type="button" class="random-any" data-domain="any" '
        'title="Choose a random language, sign language or writing system" '
        'aria-label="Choose a random language, sign language or writing system">Random</button>'
    )
    return f'<div class="home-random" role="group" aria-label="Random" hidden>{button}</div>'
