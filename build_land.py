"""Draw the backgrounds of the record-page maps: dist/map/land.svg (centred
on longitude 0) and dist/map/land-pacific.svg (centred on 150 degrees east).

Run by hand when the source or the projection changes; the output is
committed (about the size of one photo, cached by browsers once for all
pages). It needs network access to download the source once.

Source: Natural Earth 1:50m land polygons, v5.1.2 (public domain,
https://www.naturalearthdata.com/about/terms-of-use/). Projection and units:
see languoid_map.py.
"""
from pathlib import Path
import hashlib
import json
import math
import urllib.request

from languoid_map import CENTRES, project, wrap, WORLD_W

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "dist" / "map"
URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/ne_50m_land.geojson"
SHA256 = "e874b27a51d146452be360cafb3cc50c86001074a67d534113e6534682f9826b"
TOLERANCE = 0.35      # drop vertices closer than this to the last kept one (SVG units)
MIN_AREA = 0.6        # drop islands smaller than this (square SVG units)


def unwrap(ring, centre):
    """Longitudes relative to the centre, made continuous along the ring."""
    out = []
    prev = None
    for lon, lat in ring:
        rel = wrap(lon - centre)
        if prev is not None:
            while rel - prev > 180:
                rel -= 360
            while rel - prev < -180:
                rel += 360
        out.append((rel, lat))
        prev = rel
    return out


def clip(ring, keep):
    """Sutherland-Hodgman clipping of a ring against one meridian."""
    side, edge = keep
    inside = (lambda p: p[0] <= edge) if side == "max" else (lambda p: p[0] >= edge)
    out = []
    for i, cur in enumerate(ring):
        prev = ring[i - 1]
        if inside(cur):
            if not inside(prev):
                out.append(cross(prev, cur, edge))
            out.append(cur)
        elif inside(prev):
            out.append(cross(prev, cur, edge))
    return out


def cross(a, b, edge):
    t = (edge - a[0]) / (b[0] - a[0])
    return (edge, a[1] + t * (b[1] - a[1]))


def densify(ring):
    """Add points along the map edge so it projects as a curve."""
    out = []
    for i, cur in enumerate(ring):
        prev = ring[i - 1]
        if abs(prev[0]) == 180 and prev[0] == cur[0]:
            n = int(abs(cur[1] - prev[1]))
            out += [(cur[0], prev[1] + (cur[1] - prev[1]) * k / (n + 1)) for k in range(1, n + 1)]
        out.append(cur)
    return out


def pieces(ring, centre):
    """The ring cut at the map edges, in longitudes relative to the centre."""
    if centre == 0:
        return [ring]  # Natural Earth already splits land at the 180th meridian.
    u = unwrap(ring[:-1], centre)
    out = []
    for shift in (-360, 0, 360):
        r = [(x + shift, y) for x, y in u]
        r = clip(clip(r, ("max", 180.0)), ("min", -180.0))
        if len(r) >= 3:
            out.append(densify(r))
    return out


def ring_path(ring):
    pts = [project(lon, lat) for lon, lat in ring]
    pts.append(pts[0])
    kept = [pts[0]]
    for x, y in pts[1:-1]:
        if math.hypot(x - kept[-1][0], y - kept[-1][1]) >= TOLERANCE:
            kept.append((x, y))
    if len(kept) < 3:
        return ""
    area = 0.5 * abs(sum(kept[i][0] * kept[i - 1][1] - kept[i - 1][0] * kept[i][1] for i in range(len(kept))))
    if area < MIN_AREA:
        return ""
    q = [(round(x * 10), round(y * 10)) for x, y in kept]
    out = [f"M{q[0][0] / 10:g} {q[0][1] / 10:g}"]
    for (x0, y0), (x1, y1) in zip(q, q[1:]):
        out.append(f"l{(x1 - x0) / 10:g} {(y1 - y0) / 10:g}")
    return "".join(out) + "z"


def sphere_path():
    """Outline of the whole map: the 180th meridian on both sides."""
    left = [project(-180, lat) for lat in range(-90, 91)]
    right = [project(180, lat) for lat in range(90, -91, -1)]
    pts = left + right
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "z"


def main():
    raw = urllib.request.urlopen(URL, timeout=60).read()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SHA256:
        raise SystemExit(f"Unexpected SHA-256 {digest} for {URL}")
    features = json.loads(raw)["features"]
    for name, centre in CENTRES.items():
        write(name, centre, features)


def write(name, centre, features):
    paths = []
    for f in features:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            for ring in poly:
                for piece in pieces(ring, centre):
                    d = ring_path(piece)
                    if d:
                        paths.append(d)
    h = WORLD_W / 2
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" '
           f'viewBox="{-WORLD_W / 2:.1f} {-h / 2:.1f} {WORLD_W:.1f} {h:.1f}">'
           f'<!-- Natural Earth 1:50m land v5.1.2, public domain. Equal Earth projection, central meridian {centre:g}; see languoid_map.py. -->'
           f'<defs><path id="sphere" d="{sphere_path()}"/>'
           f'<path id="land" d="{"".join(paths)}"/></defs>'
           '<use href="#sphere" fill="#e4ecea"/><use href="#land" fill="#c9d3cc"/></svg>\n')
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / (name + ".svg")
    out.write_text(svg, encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)}: {len(paths)} rings, {len(svg) // 1024} KiB")


if __name__ == "__main__":
    main()
