"""Draw the backgrounds of the record-page maps.

- dist/map/land.svg (centred on longitude 0) and dist/map/land-pacific.svg
  (centred on 150 degrees east): the whole world, used by every map. Land
  from Natural Earth 1:50m, country borders from 1:50m.
- dist/map/tiles/<name>/<column>-<row>.svg: the same map cut into a grid of
  TILES_X by TILES_Y tiles at 1:10m, which dist/map-zoom.js loads for the
  part of the map in view once a visitor zooms in. Each tile also holds the
  sea inside it, so it covers the coarser world map under it completely.
- dist/map/tiles.json: the grid and the list of tiles that exist.

Borders: solid for international boundaries; dashed ("disputed") for
disputed boundaries, lines of control and indefinite or unrecognised
boundaries, following the FEATURECLA field of Natural Earth's de facto
boundary lines. Natural Earth's lease and overlay limits are left out.

Run by hand when a source or the projection changes; the output is
committed and cached by browsers once for all pages. It needs network access
to download the sources, or pass --cache DIR holding the .geojson files.

Sources: Natural Earth v5.1.2 (public domain,
https://www.naturalearthdata.com/about/terms-of-use/). Projection and units:
see languoid_map.py.
"""
from pathlib import Path
import hashlib
import json
import math
import sys
import urllib.request

from languoid_map import CENTRES, project, wrap, WORLD_W

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dist" / "map"
BASE_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/"
SOURCES = {  # file name: SHA-256
    "ne_50m_land.geojson": "e874b27a51d146452be360cafb3cc50c86001074a67d534113e6534682f9826b",
    "ne_50m_admin_0_boundary_lines_land.geojson": "2faac4f6b34386f3d21b6e018cf151f241f00e5c936d44dd17d7d9bfb147fa48",
    "ne_10m_land.geojson": "1ac90796408bc6ad6911d69448485d3c4dbf2190370080368a09976e1c9f7416",
    "ne_10m_admin_0_boundary_lines_land.geojson": "74d9c16229c095fde65943a9919e337682f044bcebccb120764f38edf3b70f4a",
}
# Detail per output: drop vertices closer than `tol` to the last kept one,
# drop islands smaller than `area`, round to `q` (all in SVG units).
WORLD = {"tol": 0.35, "area": 0.6, "q": 0.1}
TILE = {"tol": 0.06, "area": 0.004, "q": 0.02}
TILES_X, TILES_Y = 16, 8
OVERLAP = 0.3         # tiles reach this far into their neighbours, so no seam shows
DASHED = {"Disputed (please verify)", "Line of control (please verify)", "Indefinite (please verify)",
          "Indeterminant frontier", "Unrecognized"}
SOLID = {"International boundary (verify)"}


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


def simplify(pts, tol):
    kept = [pts[0]]
    for x, y in pts[1:-1]:
        if math.hypot(x - kept[-1][0], y - kept[-1][1]) >= tol:
            kept.append((x, y))
    if len(pts) > 1:
        kept.append(pts[-1])
    return kept


def path_d(pts, q, close):
    """Relative SVG path data for points already in SVG units."""
    k = 1 / q
    r = [(round(x * k), round(y * k)) for x, y in pts]
    out = [f"M{r[0][0] * q:.{_dec(q)}f} {r[0][1] * q:.{_dec(q)}f}"]
    for (x0, y0), (x1, y1) in zip(r, r[1:]):
        if (x0, y0) != (x1, y1):
            out.append(f"l{_n((x1 - x0) * q, q)} {_n((y1 - y0) * q, q)}")
    return "".join(out) + ("z" if close else "")


def _dec(q):
    return max(0, -int(math.floor(math.log10(q) + 1e-9)))


def _n(v, q):
    s = f"{v:.{_dec(q)}f}".rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"


def area(pts):
    return 0.5 * abs(sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(len(pts))))


def projected_rings(features, centre):
    """Every land ring as a list of SVG points (before simplification)."""
    out = []
    for f in features:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            for ring in poly:
                for piece in pieces(ring, centre):
                    out.append([project(lon, lat) for lon, lat in piece])
    return out


def projected_lines(features, centre):
    """Border lines as (dashed, points) in SVG units, split at the map edge."""
    out = []
    for f in features:
        cla = f["properties"].get("FEATURECLA", "")
        if cla not in SOLID and cla not in DASHED:
            continue
        g = f["geometry"]
        lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
        for line in lines:
            run, prev = [], None
            for lon, lat in line:
                rel = wrap(lon - centre)
                if prev is not None and abs(rel - prev) > 180:
                    if len(run) > 1:
                        out.append((cla in DASHED, run))
                    run = []
                run.append(project(rel, lat))
                prev = rel
            if len(run) > 1:
                out.append((cla in DASHED, run))
    return out


def clip_ring_rect(pts, x0, y0, x1, y1):
    """Sutherland-Hodgman clipping of a polygon against a rectangle."""
    def edge(points, inside, cut):
        res = []
        for i, cur in enumerate(points):
            prev = points[i - 1]
            if inside(cur):
                if not inside(prev):
                    res.append(cut(prev, cur))
                res.append(cur)
            elif inside(prev):
                res.append(cut(prev, cur))
        return res

    def at_x(e):
        return lambda a, b: (e, a[1] + (e - a[0]) / (b[0] - a[0]) * (b[1] - a[1]))

    def at_y(e):
        return lambda a, b: (a[0] + (e - a[1]) / (b[1] - a[1]) * (b[0] - a[0]), e)

    for inside, cut in ((lambda p: p[0] >= x0, at_x(x0)), (lambda p: p[0] <= x1, at_x(x1)),
                        (lambda p: p[1] >= y0, at_y(y0)), (lambda p: p[1] <= y1, at_y(y1))):
        if not pts:
            break
        pts = edge(pts, inside, cut)
    return pts


def clip_line_rect(pts, x0, y0, x1, y1):
    """Pieces of a polyline inside a rectangle (Liang-Barsky per segment)."""
    out, run = [], []
    for a, b in zip(pts, pts[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        t0, t1, ok = 0.0, 1.0, True
        for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
            if p == 0:
                if q < 0:
                    ok = False
                    break
            else:
                t = q / p
                if p < 0:
                    t0 = max(t0, t)
                else:
                    t1 = min(t1, t)
        if not ok or t0 > t1:
            if len(run) > 1:
                out.append(run)
            run = []
            continue
        s = (a[0] + t0 * dx, a[1] + t0 * dy)
        e = (a[0] + t1 * dx, a[1] + t1 * dy)
        if not run or run[-1] != s:
            if len(run) > 1:
                out.append(run)
            run = [s]
        run.append(e)
        if t1 < 1.0:
            out.append(run)
            run = []
    if len(run) > 1:
        out.append(run)
    return out


def land_d(rings, detail):
    paths = []
    for r in rings:
        if len(r) < 3:
            continue
        kept = simplify(r + [r[0]], detail["tol"])[:-1]
        if len(kept) < 3 or area(kept) < detail["area"]:
            continue
        paths.append(path_d(kept, detail["q"], True))
    return "".join(paths)


def line_d(lines, detail):
    return "".join(path_d(simplify(p, detail["tol"]), detail["q"], False) for p in lines if len(p) > 1)


def sphere_points():
    """Outline of the whole map: the 180th meridian on both sides."""
    left = [project(-180, lat / 4) for lat in range(-360, 361)]
    right = [project(180, lat / 4) for lat in range(360, -361, -1)]
    return left + right


def sphere_path():
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in sphere_points()[::4]) + "z"


def layers(sea, land, solid, dashed):
    """The <defs> body of a map file: ids sea/sphere, land, borders, disputed.

    vector-effect is set here because it is not inherited through <use>:
    border lines keep their width on screen at every zoom.
    """
    ve = ' vector-effect="non-scaling-stroke"'
    return (f'{sea}<path id="land" d="{land}"/>'
            f'<path id="borders" fill="none"{ve} d="{solid}"/>'
            f'<path id="disputed" fill="none"{ve} d="{dashed}"/>')


def load(name, cache):
    if cache:
        raw = (Path(cache) / name).read_bytes()
    else:
        raw = urllib.request.urlopen(BASE_URL + name, timeout=120).read()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SOURCES[name]:
        raise SystemExit(f"Unexpected SHA-256 {digest} for {name}")
    return json.loads(raw)["features"]


def main():
    cache = sys.argv[sys.argv.index("--cache") + 1] if "--cache" in sys.argv else None
    src = {n: load(n, cache) for n in SOURCES}
    h = WORLD_W / 2
    tw, th = WORLD_W / TILES_X, h / TILES_Y
    manifest = {"note": "Written by tools/build_land.py.", "bounds": [round(-WORLD_W / 2, 3), round(-h / 2, 3), round(WORLD_W, 3), round(h, 3)],
                "grid": [TILES_X, TILES_Y], "tiles": {}}
    sphere = sphere_points()
    for name, centre in CENTRES.items():
        world(name, centre, src)
        rings = projected_rings(src["ne_10m_land.geojson"], centre)
        lines = projected_lines(src["ne_10m_admin_0_boundary_lines_land.geojson"], centre)
        bbox_r = [(min(p[0] for p in r), min(p[1] for p in r), max(p[0] for p in r), max(p[1] for p in r)) for r in rings]
        bbox_l = [(min(p[0] for p in l), min(p[1] for p in l), max(p[0] for p in l), max(p[1] for p in l)) for _, l in lines]
        tdir = OUT / "tiles" / name
        tdir.mkdir(parents=True, exist_ok=True)
        for old in tdir.glob("*.svg"):
            old.unlink()
        written, size = [], 0
        for cx in range(TILES_X):
            for cy in range(TILES_Y):
                x0 = -WORLD_W / 2 + cx * tw - OVERLAP
                y0 = -h / 2 + cy * th - OVERLAP
                x1, y1 = x0 + tw + 2 * OVERLAP, y0 + th + 2 * OVERLAP
                sea = clip_ring_rect(sphere, x0, y0, x1, y1)
                if len(sea) < 3:
                    continue
                def hit(b):
                    return b[2] >= x0 and b[0] <= x1 and b[3] >= y0 and b[1] <= y1
                land = [clip_ring_rect(r, x0, y0, x1, y1) for r, b in zip(rings, bbox_r) if hit(b)]
                solid, dashed = [], []
                for (d, l), b in zip(lines, bbox_l):
                    if hit(b):
                        (dashed if d else solid).extend(clip_line_rect(l, x0, y0, x1, y1))
                sea_d = f'<path id="sea" d="{path_d(simplify(sea + [sea[0]], TILE["tol"])[:-1], TILE["q"], True)}"/>'
                svg = ('<svg xmlns="http://www.w3.org/2000/svg">'
                       f'<!-- Natural Earth 1:10m v5.1.2, public domain. Tile {cx}-{cy}, central meridian {centre:g}; see tools/build_land.py. -->'
                       f'<defs>{layers(sea_d, land_d(land, TILE), line_d(solid, TILE), line_d(dashed, TILE))}</defs></svg>\n')
                (tdir / f"{cx}-{cy}.svg").write_text(svg, encoding="utf-8")
                written.append(f"{cx}-{cy}")
                size += len(svg)
        manifest["tiles"][name] = written
        print(f"Wrote {tdir.relative_to(ROOT)}: {len(written)} tiles, {size // 1024} KiB")
    (OUT / "tiles.json").write_text(json.dumps(manifest, separators=(",", ":")) + "\n", encoding="utf-8")


def world(name, centre, src):
    land = land_d(projected_rings(src["ne_50m_land.geojson"], centre), WORLD)
    lines = projected_lines(src["ne_50m_admin_0_boundary_lines_land.geojson"], centre)
    solid = line_d([l for d, l in lines if not d], WORLD)
    dashed = line_d([l for d, l in lines if d], WORLD)
    h = WORLD_W / 2
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" '
           f'viewBox="{-WORLD_W / 2:.1f} {-h / 2:.1f} {WORLD_W:.1f} {h:.1f}">'
           f'<!-- Natural Earth 1:50m land and boundary lines v5.1.2, public domain. Equal Earth projection, central meridian {centre:g}; see languoid_map.py. -->'
           f'<defs>{layers(f"<path id=\"sphere\" d=\"{sphere_path()}\"/>", land, solid, dashed)}</defs>'
           '<use href="#sphere" fill="#e4ecea"/><use href="#land" fill="#c9d3cc"/>'
           '<use href="#borders" stroke="#9fb0aa" stroke-width="0.6"/><use href="#disputed" stroke="#9fb0aa" stroke-width="0.6" stroke-dasharray="3 2"/></svg>\n')
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / (name + ".svg")
    out.write_text(svg, encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)}: {len(svg) // 1024} KiB")


if __name__ == "__main__":
    main()
