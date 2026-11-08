"""Draw the backgrounds of the record-page maps.

- dist/map/land.svg: the whole world (180 degrees west to 180 degrees east),
  used by every map; the maps repeat it east and west. Land from Natural
  Earth 1:50m, country borders from 1:50m.
- dist/map/tiles/land/<column>-<row>.svg: the same map cut into a grid of
  TILES_X by TILES_Y tiles at 1:10m, which dist/map-zoom.js loads for the
  part of the map in view. Each tile also holds the sea inside it, so it
  covers the coarser world map under it completely.
- dist/map/tiles.json: the grid and the list of tiles that exist.

Shapes are made so that the maps need no trick to hide a seam: neighbouring
tiles, and the copies of the world drawn east and west of each other, overlap
with the same land and sea (OVERLAP, WRAP_OVERLAP); land cut at a line is
closed along that line piece by piece (clip_poly); land Natural Earth cut at
the 180th meridian is joined again (join_at); and no edge of a lake lies on an
edge of the land around it.

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

from locations import DIST, ROOT
from languoid_map import MAX_LAT, project, SCALE, WORLD_W

OUT = DIST / "map"
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
TILES_X, TILES_Y = 16, 16
# Shapes that meet edge to edge leave a thin light line where the browser smooths both edges,
# so neighbouring shapes overlap instead, by at least one screen pixel:
# - tiles by OVERLAP SVG units: they are drawn once the view is narrower than TILE_BELOW in
#   dist/map-zoom.js, about 2 SVG units per CSS pixel on a phone;
# - the copies of the world drawn east and west of each other by WRAP_OVERLAP: the whole
#   world on a phone is about 6 SVG units per CSS pixel.
OVERLAP = 3
WRAP_OVERLAP = 12
DASHED = {
    "Disputed (please verify)",
    "Line of control (please verify)",
    "Indefinite (please verify)",
    "Indeterminant frontier",
    "Unrecognized",
}
SOLID = {"International boundary (verify)"}


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
    for (x0, y0), (x1, y1) in zip(r, r[1:], strict=False):
        if (x0, y0) != (x1, y1):
            out.append(f"l{_n((x1 - x0) * q, q)} {_n((y1 - y0) * q, q)}")
    return "".join(out) + ("z" if close else "")


def _dec(q):
    return max(0, -int(math.floor(math.log10(q) + 1e-9)))


def _n(v, q):
    s = f"{v:.{_dec(q)}f}".rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"


def area(pts):
    return 0.5 * abs(
        sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(len(pts)))
    )


def land_polygons(features, margin):
    """Land as groups of rings in SVG units: each group is one region (outer rings and the
    holes in them, such as the Caspian Sea), to be clipped as a whole.

    Natural Earth cuts land at the 180th meridian. The land on either side is joined
    again here, and land within `margin` (SVG units) of the 180th meridian is repeated one
    world east or west, so each copy of the world reaches into its neighbour with the same
    land and no edge runs along the 180th meridian. Land is cut at MAX_LAT, where the
    square world ends.
    """
    margin_deg = math.degrees(margin / SCALE)
    near, groups = [], []
    for f in features:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            rings = [[tuple(p) for p in ring[:-1]] for ring in poly]
            lons = [p[0] for p in rings[0]]
            if max(lons) >= 180 - margin_deg or min(lons) <= -180 + margin_deg:
                near.append(rings)
            else:
                groups.append(rings)
    # One group for all land near the 180th meridian, three copies a world apart, joined
    # across the meridians at -180 and 180 degrees.
    copies = [[(x + k, y) for x, y in r] for k in (-360, 0, 360) for rings in near for r in rings]
    groups.append(join_at(copies, 0, (-180, 180)))
    out = []
    for rings in groups:
        rings = clip_poly(rings, ((1, MAX_LAT, False), (1, -MAX_LAT, True)))
        if rings:
            out.append([[project(lon, lat) for lon, lat in r] for r in rings])
    return out


def projected_lines(features):
    """Border lines as (dashed, points) in SVG units."""
    out = []
    for f in features:
        cla = f["properties"].get("FEATURECLA", "")
        if cla not in SOLID and cla not in DASHED:
            continue
        g = f["geometry"]
        lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
        for line in lines:
            if len(line) > 1:
                out.append((cla in DASHED, [project(lon, lat) for lon, lat in line]))
    return out


def stitch(chains, axis):
    """Close open chains into rings. Each chain starts and ends on a line where coordinate
    `axis` is constant; along each line the chain ends and starts are sorted and paired
    (1st with 2nd, 3rd with 4th, ...), and the ring runs along the line between a pair.
    For a region, the boundary on the line lies exactly between those pairs.
    """
    other = 1 - axis
    marks = {}
    for n, c in enumerate(chains):
        marks.setdefault(c[-1][axis], []).append((c[-1][other], 0, n))  # an end
        marks.setdefault(c[0][axis], []).append((c[0][other], 1, n))  # a start
    follow = {}
    for line in marks.values():
        line.sort()
        if len(line) % 2:
            raise ValueError("an odd number of crossings on one line")
        for a, b in zip(line[0::2], line[1::2], strict=True):
            if a[1] == b[1]:
                raise ValueError("crossings do not alternate; the rings do not bound a region")
            end, start = (a, b) if a[1] == 0 else (b, a)
            follow[end[2]] = start[2]
    out, used = [], set()
    for n in range(len(chains)):
        if n in used:
            continue
        r, m = [], n
        while m not in used:
            used.add(m)
            r.extend(p for p in chains[m] if not r or p != r[-1])
            m = follow[m]
        if len(r) > 1 and r[0] == r[-1]:
            r.pop()
        if len(r) >= 3:
            out.append(r)
    return out


def clip_poly(rings, edges):
    """A region (a list of rings) cut by straight lines, keeping one side of each.

    edges: (axis, value, keep_above). Every piece is closed along the line on its own, so
    no zero-width run joins two pieces across what lies between them (Sutherland-Hodgman
    did, which drew lines across enclosed seas). Holes that a line cuts become part of the
    outline of the land around them, so no edge of a hole lies on an edge of the land.
    """
    for axis, edge, above in edges:
        side = 1 if above else -1
        other = 1 - axis

        def inside(p, axis=axis, edge=edge, side=side):
            return side * (p[axis] - edge) >= 0

        def cut(a, b, axis=axis, other=other, edge=edge):
            t = (edge - a[axis]) / (b[axis] - a[axis])
            q = [0.0, 0.0]
            q[axis] = edge
            q[other] = a[other] + t * (b[other] - a[other])
            return tuple(q)

        whole, chains = [], []
        for ring in rings:
            flags = [inside(p) for p in ring]
            if all(flags):
                whole.append(ring)
                continue
            if not any(flags):
                continue
            # Start at an outside point, so every chain begins with an entry and ends with an exit.
            k = flags.index(False)
            ring, flags = ring[k:] + ring[:k], flags[k:] + flags[:k]
            run = None
            for i in range(1, len(ring) + 1):
                prev, cur = ring[i - 1], ring[i % len(ring)]
                f_prev, f_cur = flags[i - 1], flags[i % len(ring)]
                if f_cur and not f_prev:
                    run = [cut(prev, cur)]
                if f_cur:
                    if cur != run[-1]:
                        run.append(cur)
                elif f_prev:
                    x = cut(prev, cur)
                    if x != run[-1]:
                        run.append(x)
                    chains.append(run)
                    run = None
        rings = whole + stitch(chains, axis)
        if not rings:
            break
    return rings


def join_at(rings, axis, lines):
    """One region from rings that meet edge to edge on straight lines (land that Natural
    Earth cut at the 180th meridian, with its copies a world away): the edges that lie on
    the lines are taken out and the rest joined, running along a line only where land
    lies on one side of it.
    """
    whole, chains = [], []
    for ring in rings:

        def on(i, ring=ring):
            a, b = ring[i - 1], ring[i]
            return a[axis] == b[axis] and a[axis] in lines

        cuts = [i for i in range(len(ring)) if on(i)]
        if not cuts:
            whole.append(ring)
            continue
        # Start right after an edge on a line; each chain runs to the next such edge.
        k = cuts[0]
        ring = ring[k:] + ring[:k]
        run = [ring[0]]
        for i in range(1, len(ring) + 1):
            if on(i % len(ring), ring):
                if len(run) > 1:
                    chains.append(run)
                run = [ring[i % len(ring)]]
            else:
                run.append(ring[i % len(ring)])
    return whole + stitch(chains, axis)


def rect_edges(x0, y0, x1, y1):
    return ((0, x0, True), (0, x1, False), (1, y0, True), (1, y1, False))


def clip_line_rect(pts, x0, y0, x1, y1):
    """Pieces of a polyline inside a rectangle (Liang-Barsky per segment)."""
    out, run = [], []
    for a, b in zip(pts, pts[1:], strict=False):
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
    return "".join(
        path_d(simplify(p, detail["tol"]), detail["q"], False) for p in lines if len(p) > 1
    )


def sphere_points():
    """Outline of the whole map: the square Web Mercator world."""
    h = WORLD_W / 2
    return [(-h, -h), (h, -h), (h, h), (-h, h)]


def sphere_path():
    h = WORLD_W / 2
    return f"M{-h:.1f} {-h:.1f}H{h:.1f}V{h:.1f}H{-h:.1f}z"


def sea_path():
    """The sea behind the copies of the world: the world reaching WRAP_OVERLAP into each
    neighbour, as the land does (land_polygons)."""
    h, w = WORLD_W / 2, WORLD_W / 2 + WRAP_OVERLAP
    return f"M{-w:.1f} {-h:.1f}H{w:.1f}V{h:.1f}H{-w:.1f}z"


def layers(sea, land, solid, dashed):
    """The <defs> body of a map file: ids sea/sphere, land, borders, disputed.

    vector-effect is set here because it is not inherited through <use>:
    border lines keep their width on screen at every zoom.
    """
    ve = ' vector-effect="non-scaling-stroke"'
    return (
        f'{sea}<path id="land" d="{land}"/>'
        f'<path id="borders" fill="none"{ve} d="{solid}"/>'
        f'<path id="disputed" fill="none"{ve} d="{dashed}"/>'
    )


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
    h = WORLD_W
    tw, th = WORLD_W / TILES_X, h / TILES_Y
    manifest = {
        "note": "Written by tools/build_land.py.",
        "bounds": [round(-WORLD_W / 2, 3), round(-h / 2, 3), round(WORLD_W, 3), round(h, 3)],
        "grid": [TILES_X, TILES_Y],
        "tiles": {},
    }
    sphere = sphere_points()
    name = "land"
    world(name, src)
    groups = land_polygons(src["ne_10m_land.geojson"], OVERLAP)
    lines = projected_lines(src["ne_10m_admin_0_boundary_lines_land.geojson"])
    bbox_g = [
        (
            min(p[0] for r in g for p in r),
            min(p[1] for r in g for p in r),
            max(p[0] for r in g for p in r),
            max(p[1] for r in g for p in r),
        )
        for g in groups
    ]
    bbox_l = [
        (
            min(p[0] for p in line),
            min(p[1] for p in line),
            max(p[0] for p in line),
            max(p[1] for p in line),
        )
        for _, line in lines
    ]
    for old in (OUT / "tiles").glob("*/*.svg"):
        old.unlink()
    for d in (OUT / "tiles").glob("*"):
        if d.is_dir() and d.name != name:
            d.rmdir()
    for old in OUT.glob("*.svg"):
        if old.stem != name:
            old.unlink()
    tdir = OUT / "tiles" / name
    tdir.mkdir(parents=True, exist_ok=True)
    written, size = [], 0
    for cx in range(TILES_X):
        for cy in range(TILES_Y):
            x0 = -WORLD_W / 2 + cx * tw - OVERLAP
            y0 = -h / 2 + cy * th - OVERLAP
            x1, y1 = x0 + tw + 2 * OVERLAP, y0 + th + 2 * OVERLAP
            sea = clip_poly([sphere], rect_edges(x0, y0, x1, y1))
            if not sea:
                continue
            sea = sea[0]

            # Defined and called within one loop iteration, so the loop variables it reads
            # are always the current ones (the noqa: B023 marks below).
            def hit(b):
                return b[2] >= x0 and b[0] <= x1 and b[3] >= y0 and b[1] <= y1  # noqa: B023

            land = [
                piece
                for g, b in zip(groups, bbox_g, strict=False)
                if hit(b)
                for piece in clip_poly(g, rect_edges(x0, y0, x1, y1))
            ]
            solid, dashed = [], []
            for (d, line), b in zip(lines, bbox_l, strict=False):
                if hit(b):
                    (dashed if d else solid).extend(clip_line_rect(line, x0, y0, x1, y1))
            sea_d = f'<path id="sea" d="{path_d(sea, TILE["q"], True)}"/>'
            svg = (
                '<svg xmlns="http://www.w3.org/2000/svg">'
                f"<!-- Natural Earth 1:10m v5.1.2, public domain. Tile {cx}-{cy}, Web Mercator; see tools/build_land.py. -->"
                f"<defs>{layers(sea_d, land_d(land, TILE), line_d(solid, TILE), line_d(dashed, TILE))}</defs></svg>\n"
            )
            (tdir / f"{cx}-{cy}.svg").write_text(svg, encoding="utf-8")
            written.append(f"{cx}-{cy}")
            size += len(svg)
    manifest["tiles"][name] = written
    print(f"Wrote {tdir.relative_to(ROOT)}: {len(written)} tiles, {size // 1024} KiB")
    (OUT / "tiles.json").write_text(
        json.dumps(manifest, separators=(",", ":")) + "\n", encoding="utf-8"
    )


def world(name, src):
    h = WORLD_W / 2 + WRAP_OVERLAP
    land = land_d(
        [
            piece
            for g in land_polygons(src["ne_50m_land.geojson"], WRAP_OVERLAP)
            for piece in clip_poly(g, ((0, -h, True), (0, h, False)))
        ],
        WORLD,
    )
    lines = projected_lines(src["ne_50m_admin_0_boundary_lines_land.geojson"])
    solid = line_d([line for d, line in lines if not d], WORLD)
    dashed = line_d([line for d, line in lines if d], WORLD)
    h = WORLD_W
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{-WORLD_W / 2:.1f} {-h / 2:.1f} {WORLD_W:.1f} {h:.1f}">'
        "<!-- Natural Earth 1:50m land and boundary lines v5.1.2, public domain. Web Mercator; see languoid_map.py. -->"
        f"<defs>{layers(f'<path id="sphere" d="{sphere_path()}"/><path id="sea" d="{sea_path()}"/>', land, solid, dashed)}</defs>"
        '<use href="#sphere" fill="#e4ecea"/><use href="#land" fill="#c9d3cc"/>'
        '<use href="#borders" stroke="#9fb0aa" stroke-width="0.6"/><use href="#disputed" stroke="#9fb0aa" stroke-width="0.6" stroke-dasharray="3 2"/></svg>\n'
    )
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / (name + ".svg")
    out.write_text(svg, encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)}: {len(svg) // 1024} KiB")


if __name__ == "__main__":
    main()
