"""The Collective's network map: a minimalist Equal Earth world map with one point
per institution and arcs from Toronto, where the Collective is based.

Used by build_site.py; it returns inline SVG so the page font and tooltips apply.
Land: Natural Earth 110m land (public domain), content/world-land.geojson.
Coordinates: content/places.json, one entry per institution in people.json.
"""
import html
import math
import sys
from collections import OrderedDict

A1, A2, A3, A4 = 1.340264, -0.081106, 0.000893, 0.003796
M = math.sqrt(3) / 2
W = 1000.0
XMAX = 2.7066297319215   # Equal Earth x at lon 180, lat 0
S = W / (2 * XMAX)
LAT_TOP, LAT_BOTTOM = 74.0, -50.0


def _ee(lon, lat):
    lam, phi = math.radians(lon), math.radians(lat)
    t = math.asin(M * math.sin(phi))
    t2 = t * t
    t6 = t2 * t2 * t2
    x = lam * math.cos(t) / (M * (A1 + 3 * A2 * t2 + t6 * (7 * A3 + 9 * A4 * t2)))
    y = t * (A1 + A2 * t2 + t6 * (A3 + A4 * t2))
    return x, y


_, Y_TOP = _ee(0, LAT_TOP)
_, Y_BOTTOM = _ee(0, LAT_BOTTOM)
H = (Y_TOP - Y_BOTTOM) * S


def project(lon, lat):
    x, y = _ee(lon, lat)
    return (x + XMAX) * S, (Y_TOP - y) * S


def _land_path(land):
    parts = []
    for f in land['features']:
        g = f['geometry']
        polys = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
        for poly in polys:
            for ring in poly:
                if max(p[1] for p in ring) < LAT_BOTTOM:
                    continue  # Antarctica
                pts = [project(lon, max(min(lat, 89), -89)) for lon, lat in ring]
                d, last = [], None
                for x, y in pts:
                    q = (round(x, 1), round(y, 1))
                    if q != last:
                        d.append(f'{q[0]:g},{q[1]:g}')
                        last = q
                if len(d) > 2:
                    parts.append('M' + 'L'.join(d) + 'Z')
    return ''.join(parts)


def network_map(people, places, land, hub='Toronto Metropolitan University', link=lambda p: ''):
    esc = lambda s: html.escape(str(s), quote=True)
    sites = OrderedDict()
    for p in people:
        sites.setdefault(p['institution'], []).append(p)
    pts = {inst: project(places[inst]['lon'], places[inst]['lat']) for inst in sites}
    hx, hy = pts[hub]

    arcs = []
    for inst, (x, y) in pts.items():
        if inst == hub:
            continue
        dx, dy = x - hx, y - hy
        dist = math.hypot(dx, dy)
        if dist < 1:
            continue
        # bow each arc upward, more for longer links
        k = 0.22 if dist > 40 else 0.35
        nx, ny = -dy / dist, dx / dist
        if ny > 0:
            nx, ny = -nx, -ny
        cx, cy = (hx + x) / 2 + nx * dist * k, (hy + y) / 2 + ny * dist * k
        arcs.append(f'<path d="M{hx:.1f},{hy:.1f}Q{cx:.1f},{cy:.1f} {x:.1f},{y:.1f}"/>')

    # crop to the network, with room for labels
    xs = [x for x, _ in pts.values()]
    ys = [y for _, y in pts.values()]
    x0, x1 = min(xs) - 70, max(xs) + 95
    y0, y1 = min(ys) - 45, max(ys) + 35
    FS = 13.0                      # label size in map units
    rad = {inst: 2.8 + 1.6 * math.sqrt(len(sites[inst]) - 1) for inst in sites}

    def box(x, y, w, h):
        return (x, y, x + w, y + h)

    def hit(a, b):
        return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])

    taken = [box(pts[i][0] - rad[i], pts[i][1] - rad[i], 2 * rad[i], 2 * rad[i]) for i in sites]
    dots, labels, seen = [], [], set()
    order = sorted(sites, key=lambda i: (i != hub, -len(sites[i]), i))
    for inst in order:
        x, y = pts[inst]
        r = rad[inst]
        names = ', '.join(p['name'] for p in sites[inst])
        ring = f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r + 4:.1f}" class="nm-ring"/>' if inst == hub else ''
        dots.append(f'<g class="nm-site"><title>{esc(inst)}: {esc(names)}</title>{ring}'
                    f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" class="nm-dot"/></g>')
    for inst in order:
        city = places[inst]['city']
        if city in seen:
            continue
        seen.add(city)
        x, y = pts[inst]
        r = rad[inst] + (4 if inst == hub else 0)
        w, h = len(city) * FS * 0.56 + 2, FS
        own = box(x - rad[inst], y - rad[inst], 2 * rad[inst], 2 * rad[inst])
        cands = [('start', x + r + 5, y + FS * 0.35), ('end', x - r - 5, y + FS * 0.35),
                 ('start', x + r + 3, y + r + FS + 1), ('start', x + r + 3, y - r - 4),
                 ('end', x - r - 3, y + r + FS + 1), ('end', x - r - 3, y - r - 4)]
        # a point with a close neighbour just east of it labels to the west first,
        # so its name never sits beside the neighbour's dot (Lisbon next to Évora)
        if any(0 < pts[j][0] - x < 10 and abs(pts[j][1] - y) < 8 for j in sites if j != inst):
            cands[0], cands[1] = cands[1], cands[0]
        if inst == hub:
            cands = [('start', x + r + 3, y + r + FS + 2)] + cands
        # further out, joined to the point by a short leader line
        # (not for the points packed round Toronto, which the hover names instead)
        if math.hypot(x - hx, y - hy) > 60:
            for dy in (-20, 20, -34, 34):
                cands += [('start', x + r + 12, y + dy + FS * 0.35), ('end', x - r - 12, y + dy + FS * 0.35)]
        for anchor, lx, ly in cands:
            bx = lx if anchor == 'start' else lx - w
            bb = box(bx, ly - FS * 0.8, w, h)
            if bb[0] < x0 or bb[2] > x1 or bb[1] < y0 or bb[3] > y1:
                continue
            if any(hit(bb, t) for t in taken if t != own):
                continue
            taken.append(bb)
            cls = 'nm-label nm-hub' if inst == hub else 'nm-label'
            if abs(ly - FS * 0.35 - y) > r + FS:
                ex = lx - 2 if anchor == 'start' else lx + 2
                labels.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{ex:.1f}" y2="{ly - FS * 0.35:.1f}" class="nm-lead"/>')
            labels.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" class="{cls}">{esc(city)}</text>')
            break
        else:
            pass  # no room: the point keeps its hover title

    n_inst, n_people = len(sites), len(people)
    title = f'Map of the Spatial Intelligence Collective: {n_people} members at {n_inst} institutions, linked to Toronto'
    return (f'<svg class="netmap" viewBox="{x0:.0f} {y0:.0f} {x1 - x0:.0f} {y1 - y0:.0f}" role="img" aria-label="{esc(title)}" '
            f'xmlns="http://www.w3.org/2000/svg"><title>{esc(title)}</title>'
            f'<path class="nm-land" d="{_land_path(land)}"/>'
            f'<g class="nm-arcs">{"".join(arcs)}</g>'
            f'<g class="nm-sites">{"".join(dots)}</g>'
            f'<g>{"".join(labels)}</g></svg>')
