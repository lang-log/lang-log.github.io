"""The big logo of the top page (dist/components/big-logo/), with "by yoshi" under it."""

from site_brand import by_yoshi


def big_logo():
    return (
        '<h1 class="home-logo"><svg class="logo" role="img" aria-label="LANG LOG"><use href="logo.svg#logo"/></svg></h1>'
        + by_yoshi("p", "home-by")
    )
