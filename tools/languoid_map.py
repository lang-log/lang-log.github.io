"""Static distribution maps for the record pages under dist/<family>/.../<language>/.

Each map is a small inline SVG: the shared background dist/map/land.svg
(drawn by build_land.py) is referenced with <use>, so it is downloaded once
and cached, and each page adds only its own points. No JavaScript.

Projection: Equal Earth (Savric, Patterson and Jenny 2018). Two backgrounds
exist: central meridian 0 (land.svg) and 150 degrees east (land-pacific.svg),
used when the points lie around the 180th meridian (for example Oceanic). One unit of the SVG coordinate system is SCALE times the projection's unit
radius; north is up (y grows downwards, as in SVG).

Points are Glottolog's representative coordinates (one per record). They are
not the area where a language is spoken.
"""
from html import escape
import math

SCALE = 360.0
A1, A2, A3, A4 = 1.340264, -0.081106, 0.000893, 0.003796
M = math.sqrt(3) / 2

# Extent of the whole map in SVG units.
WORLD_W = 2 * SCALE * 2 * math.sqrt(3) * math.pi / (3 * A1)
WORLD_H = 2 * SCALE * 1.3173627591574


CENTRES = {"land": 0.0, "land-pacific": 150.0}


def wrap(lon):
    """Longitude in degrees to the range [-180, 180)."""
    return (lon + 180.0) % 360.0 - 180.0


def project(lon, lat, centre=0.0):
    """Longitude and latitude in degrees to SVG x, y (origin at the centre).

    The longitude is taken relative to the central meridian and wrapped,
    except that exactly +-180 relative to it is kept (the map's edges).
    """
    rel = lon - centre
    if abs(rel) != 180.0:
        rel = wrap(rel)
    lam = math.radians(rel)
    th = math.asin(M * math.sin(math.radians(lat)))
    t2 = th * th
    t6 = t2 * t2 * t2
    x = 2 * math.sqrt(3) * lam * math.cos(th) / (3 * (A1 + 3 * A2 * t2 + t6 * (7 * A3 + 9 * A4 * t2)))
    y = th * (A1 + A2 * t2 + t6 * (A3 + A4 * t2))
    return x * SCALE, -y * SCALE


ASPECT = 2.0          # width / height of every map
MIN_W = 240.0         # smallest view, in SVG units (about 45 degrees of longitude at the equator)
PAD = 0.12            # margin around the points, as a share of their extent


def _view(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w = max((x1 - x0) * (1 + 2 * PAD), MIN_W)
    h = max((y1 - y0) * (1 + 2 * PAD), MIN_W / ASPECT)
    if w / h < ASPECT:
        w = h * ASPECT
    else:
        h = w / ASPECT
    if w >= WORLD_W:
        return -WORLD_W / 2, -WORLD_W / ASPECT / 2, WORLD_W, WORLD_W / ASPECT
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    # Keep the view on the map where possible.
    cx = min(max(cx, -WORLD_W / 2 + w / 2), WORLD_W / 2 - w / 2)
    if h < WORLD_H:
        cy = min(max(cy, -WORLD_H / 2 + h / 2), WORLD_H / 2 - h / 2)
    else:
        cy = 0.0
    return cx - w / 2, cy - h / 2, w, h


def _num(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def _width(points, centre):
    xs = [project(lon, lat, centre)[0] for lon, lat in points]
    return max(xs) - min(xs)


def map_svg(map_dir, main, context=(), self_point=None, label=""):
    """Return an inline <svg> map, or "" when there is nothing to place.

    map_dir: relative URL of the map/ directory from the page, ending in "/".
    main: (lon, lat) points of the record's own members, drawn strong.
    context: points of related records (for example sister languages), drawn faint.
    self_point: the record's own point, drawn largest.
    """
    lonlat = list(main) + ([self_point] if self_point else [])
    if not lonlat:
        return ""
    name = "land"
    if _width(lonlat, CENTRES["land-pacific"]) < 0.8 * _width(lonlat, CENTRES["land"]):
        name = "land-pacific"
    c = CENTRES[name]
    main = [project(lon, lat, c) for lon, lat in main]
    context = [project(lon, lat, c) for lon, lat in context]
    own = project(*self_point, c) if self_point else None
    focus = main + ([own] if own else [])
    if not focus:
        return ""
    vx, vy, vw, vh = _view(focus)
    r = vw / 200                      # point radius scales with the view
    show_inset = vw < WORLD_W * 0.5

    def circles(pts, rad):
        seen = set()
        out = []
        for x, y in pts:
            key = (round(x / rad), round(y / rad))   # drop points hidden under others
            if key in seen:
                continue
            seen.add(key)
            out.append(f'<circle cx="{_num(x)}" cy="{_num(y)}" r="{_num(rad)}"/>')
        return "".join(out)

    land = escape(map_dir + name + ".svg")
    parts = [
        f'<svg class="lmap" viewBox="{_num(vx)} {_num(vy)} {_num(vw)} {_num(vh)}" role="img" aria-label="{escape(label)}" preserveAspectRatio="xMidYMid meet">',
        f'<title>{escape(label)}</title>',
        f'<use class="lmap-sphere" href="{land}#sphere"/><use class="lmap-land" href="{land}#land"/>',
    ]
    if context:
        parts.append(f'<g class="lmap-ctx">{circles(context, r * 0.8)}</g>')
    if main:
        parts.append(f'<g class="lmap-main">{circles(main, r)}</g>')
    if own:
        parts.append(f'<g class="lmap-self"><circle cx="{_num(own[0])}" cy="{_num(own[1])}" r="{_num(r * 2.4)}"/></g>')
    if show_inset:
        # Locator: the whole world in the corner, with the shown area marked.
        iw = vw * 0.22
        ih = iw / ASPECT
        ix, iy = vx + vw - iw - vw * 0.015, vy + vh - ih - vw * 0.015
        parts.append(
            f'<g class="lmap-inset"><svg x="{_num(ix)}" y="{_num(iy)}" width="{_num(iw)}" height="{_num(ih)}" '
            f'viewBox="{_num(-WORLD_W / 2)} {_num(-WORLD_W / ASPECT / 2)} {_num(WORLD_W)} {_num(WORLD_W / ASPECT)}">'
            f'<use class="lmap-sphere" href="{land}#sphere"/><use class="lmap-land" href="{land}#land"/>'
            f'<rect x="{_num(vx)}" y="{_num(vy)}" width="{_num(vw)}" height="{_num(vh)}"/></svg></g>'
        )
    parts.append("</svg>")
    return "".join(parts)
