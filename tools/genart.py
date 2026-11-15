#!/usr/bin/env python3
"""Deterministic generative grayscale artwork for the Spatial Intelligence Collective site.
Everything is seeded, so rebuilds are byte-identical."""
import math, random, os

OUT = os.path.join(os.path.dirname(__file__), '..', 'assets', 'art')
os.makedirs(OUT, exist_ok=True)

def f(v):  # compact float
    s = f"{v:.2f}".rstrip('0').rstrip('.')
    return s if s not in ('-0', '') else '0'

# ---------------------------------------------------------------- scalar field
class Field:
    """Sum of gaussian bumps -> smooth scalar field. Used for contours."""
    def __init__(self, rng, w, h, n=14, smin=.10, smax=.34):
        self.b = []
        for _ in range(n):
            self.b.append((rng.uniform(-.15, 1.15) * w, rng.uniform(-.15, 1.15) * h,
                           rng.uniform(smin, smax) * max(w, h),
                           rng.choice([1, 1, 1, -1]) * rng.uniform(.5, 1.4)))
    def __call__(self, x, y):
        t = 0.0
        for cx, cy, s, a in self.b:
            dx, dy = x - cx, y - cy
            t += a * math.exp(-(dx * dx + dy * dy) / (2 * s * s))
        return t

def marching(field, w, h, level, nx=150, ny=110):
    """Marching squares -> list of polylines at iso `level`."""
    gx, gy = w / nx, h / ny
    val = [[field(i * gx, j * gy) for j in range(ny + 1)] for i in range(nx + 1)]
    segs = []
    def ip(a, b, va, vb):
        t = 0 if vb == va else (level - va) / (vb - va)
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    for i in range(nx):
        for j in range(ny):
            p = [(i*gx, j*gy), ((i+1)*gx, j*gy), ((i+1)*gx, (j+1)*gy), (i*gx, (j+1)*gy)]
            v = [val[i][j], val[i+1][j], val[i+1][j+1], val[i][j+1]]
            idx = sum((1 << k) for k in range(4) if v[k] > level)
            if idx in (0, 15): continue
            e = {}
            for k in range(4):
                k2 = (k + 1) % 4
                if (v[k] > level) != (v[k2] > level):
                    e[k] = ip(p[k], p[k2], v[k], v[k2])
            pts = list(e.values())
            if len(pts) == 2: segs.append((pts[0], pts[1]))
            elif len(pts) == 4:
                segs.append((pts[0], pts[1])); segs.append((pts[2], pts[3]))
    # stitch segments into polylines
    key = lambda p: (round(p[0], 3), round(p[1], 3))
    adj = {}
    for a, b in segs:
        adj.setdefault(key(a), []).append((a, b))
        adj.setdefault(key(b), []).append((b, a))
    used, lines = set(), []
    for a, b in segs:
        if (key(a), key(b)) in used or (key(b), key(a)) in used: continue
        line = [a, b]; used.add((key(a), key(b)))
        for _ in range(2):                       # walk forward, then reverse
            while True:
                cur = line[-1]; nxt = None
                for s, t in adj.get(key(cur), []):
                    if (key(s), key(t)) in used or (key(t), key(s)) in used: continue
                    nxt = t; used.add((key(s), key(t))); break
                if nxt is None: break
                line.append(nxt)
            line.reverse()
        if len(line) > 3: lines.append(line)
    return lines

def path(pts, prec=1):
    d = f"M{f(pts[0][0])} {f(pts[0][1])}"
    for x, y in pts[1:]: d += f"L{f(x)} {f(y)}"
    return d

def svg(w, h, body, extra=''):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'fill="none" role="img">{extra}{body}</svg>')

def write(name, s):
    p = os.path.join(OUT, name)
    open(p, 'w').write(s)
    print(f"  {name:34s} {len(s)/1024:6.1f} KB")

# ---------------------------------------------------------------- primitives
def contours(rng, w, h, levels, stroke=.7, op=.55, n=14, smin=.10, smax=.34):
    fd = Field(rng, w, h, n, smin, smax)
    out = []
    for lv in levels:
        for ln in marching(fd, w, h, lv):
            out.append(f'<path d="{path(ln)}"/>')
    return (f'<g stroke="#0f0f12" stroke-width="{stroke}" opacity="{op}" '
            f'stroke-linejoin="round">' + ''.join(out) + '</g>')

def scatter(rng, w, h, n, rmin=.6, rmax=2.6, op=.7, bias=None, dark=0):
    """bias(x,y)->0..1 density weight. dark = count of large black nodes."""
    pts, tries = [], 0
    while len(pts) < n and tries < n * 40:
        tries += 1
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        if bias and rng.random() > bias(x, y): continue
        pts.append((x, y))
    o = []
    for i, (x, y) in enumerate(pts):
        r = rmin + (rmax - rmin) * rng.random() ** 2.2
        g = int(20 + 120 * rng.random())
        o.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="rgb({g},{g},{g+3})"/>')
    return f'<g opacity="{op}">' + ''.join(o) + '</g>', pts

def network(rng, nodes, k=2, stroke=.55, op=.5, rmin=2.2, rmax=5.5, colr='#0f0f12'):
    """Connect each node to k nearest neighbours; return edges+nodes markup."""
    E = set()
    for i, a in enumerate(nodes):
        d = sorted(((math.dist(a, b), j) for j, b in enumerate(nodes) if j != i))[:k]
        for _, j in d: E.add((min(i, j), max(i, j)))
    ed = ''.join(f'<line x1="{f(nodes[i][0])}" y1="{f(nodes[i][1])}" '
                 f'x2="{f(nodes[j][0])}" y2="{f(nodes[j][1])}"/>' for i, j in E)
    nd = ''
    for x, y in nodes:
        r = rmin + (rmax - rmin) * rng.random() ** 1.8
        nd += f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{colr}"/>'
    return (f'<g stroke="{colr}" stroke-width="{stroke}" opacity="{op}">{ed}</g>'
            f'<g opacity=".92">{nd}</g>')

def mesh(w, h, x0, y0, cw, ch, cols, rows, skew=.0, stroke=.45, op=.28):
    o = []
    for i in range(cols + 1):
        x = x0 + i * cw
        o.append(f'<line x1="{f(x)}" y1="{f(y0)}" x2="{f(x + skew*ch*rows)}" y2="{f(y0+ch*rows)}"/>')
    for j in range(rows + 1):
        y = y0 + j * ch
        o.append(f'<line x1="{f(x0 + skew*j*ch)}" y1="{f(y)}" x2="{f(x0 + skew*j*ch + cw*cols)}" y2="{f(y)}"/>')
    return f'<g stroke="#0f0f12" stroke-width="{stroke}" opacity="{op}">' + ''.join(o) + '</g>'

def fade(id_, cx, cy, r):
    return (f'<defs><radialGradient id="{id_}" cx="{cx}" cy="{cy}" r="{r}">'
            f'<stop offset="0" stop-color="#fff" stop-opacity="1"/>'
            f'<stop offset=".55" stop-color="#fff" stop-opacity=".85"/>'
            f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
            f'<mask id="m{id_}"><rect width="100%" height="100%" fill="url(#{id_})"/></mask></defs>')
