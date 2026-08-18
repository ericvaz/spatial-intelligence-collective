#!/usr/bin/env python3
import math, random, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from genart import *

W, H = 300, 180

# ------------------------------------------------ Voronoi (half-plane clipping)
def clip(poly, a, b):
    """Keep the half-plane closer to a than b."""
    mx, my = (a[0]+b[0])/2, (a[1]+b[1])/2
    nx, ny = b[0]-a[0], b[1]-a[1]
    side = lambda p: (p[0]-mx)*nx + (p[1]-my)*ny
    out = []
    for i in range(len(poly)):
        c, d = poly[i], poly[(i+1) % len(poly)]
        sc, sd = side(c), side(d)
        if sc <= 0: out.append(c)
        if (sc <= 0) != (sd <= 0):
            t = sc / (sc - sd)
            out.append((c[0]+(d[0]-c[0])*t, c[1]+(d[1]-c[1])*t))
    return out

def voronoi(pts, bbox):
    x0, y0, x1, y1 = bbox
    cells = []
    for a in pts:
        poly = [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
        for b in pts:
            if b is a: continue
            poly = clip(poly, a, b)
            if not poly: break
        if poly: cells.append((a, poly))
    return cells

def choropleth(seed, n=54, blob=True):
    """Regional mosaic - reads as a choropleth of administrative regions."""
    rng = random.Random(seed)
    cx, cy = W/2, H/2
    pts = []
    while len(pts) < n:
        x, y = rng.uniform(6, W-6), rng.uniform(6, H-6)
        if blob:
            # soft irregular landmass silhouette
            a = math.atan2(y-cy, x-cx)
            rad = 1 + .22*math.sin(3*a+1.1) + .15*math.sin(5*a+2.4) + .1*math.sin(7*a)
            if ((x-cx)/(W*.44))**2 + ((y-cy)/(H*.46))**2 > rad**2: continue
        pts.append((x, y))
    o = []
    for (px, py), poly in voronoi(pts, (0, 0, W, H)):
        # value gradient + noise -> plausible spatial autocorrelation
        v = .5 + .5*math.sin(px/58) * math.cos(py/44) + rng.uniform(-.22, .22)
        g = int(max(96, min(247, 252 - v*138)))
        d = 'M' + 'L'.join(f'{f(x)} {f(y)}' for x, y in poly) + 'Z'
        o.append(f'<path d="{d}" fill="rgb({g},{g},{g+2})" stroke="#fff" stroke-width=".8"/>')
    return svg(W, H, ''.join(o))

def surface(seed):
    """Wireframe terrain - simulation surface / model output."""
    rng = random.Random(seed)
    fd = Field(rng, W, H, 10, .16, .34)
    o = []
    rows = 26
    for j in range(rows):
        t = j / (rows - 1)
        y0 = 34 + t * 118
        pts = []
        for i in range(81):
            x = i * W / 80
            z = fd(x, y0) * 20 * (1 - .35*t)
            pts.append((x * (.72 + .28*t) + (1-t) * W * .14, y0 - z))
        o.append(f'<path d="{path(pts)}" opacity="{f(.28 + .42*t)}"/>')
    return svg(W, H, f'<g stroke="#0f0f12" stroke-width=".7" fill="none" '
                     f'stroke-linejoin="round">{"".join(o)}</g>')

def netgraph(seed, n=46, k=2):
    rng = random.Random(seed)
    pts = [(rng.uniform(18, W-18), rng.uniform(16, H-16)) for _ in range(n)]
    return svg(W, H, network(rng, pts, k=k, stroke=.6, op=.45, rmin=2.0, rmax=6.2))

def pointpattern(seed, n=560):
    rng = random.Random(seed)
    cl = [(rng.uniform(50, 250), rng.uniform(40, 145), rng.uniform(14, 38)) for _ in range(9)]
    bias = lambda x, y: min(1., .06 + sum(
        math.exp(-math.dist((x, y), (cx, cy))**2/(2*s*s)) for cx, cy, s in cl))
    d, _ = scatter(random.Random(seed+1), W, H, n, .5, 2.6, .82, bias)
    return svg(W, H, d)

def gamegrid(seed):
    """Strategic interaction lattice - best-response / equilibrium flow."""
    rng = random.Random(seed)
    nodes, o = [], []
    for i in range(7):
        for j in range(5):
            nodes.append((26 + i*41 + rng.uniform(-5,5), 22 + j*34 + rng.uniform(-5,5)))
    for i, a in enumerate(nodes):
        for j, b in enumerate(nodes):
            if j <= i: continue
            d = math.dist(a, b)
            if d < 48:
                o.append(f'<line x1="{f(a[0])}" y1="{f(a[1])}" x2="{f(b[0])}" y2="{f(b[1])}" '
                         f'opacity="{f(max(.08, .46 - d/140))}"/>')
    nd = ''
    for x, y in nodes:
        r = 1.8 + 4.2*rng.random()**2
        nd += f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="#141418"/>'
    # a few directed best-response arrows
    for _ in range(9):
        a, b = rng.choice(nodes), rng.choice(nodes)
        if 30 < math.dist(a, b) < 95:
            o.append(f'<path d="M{f(a[0])} {f(a[1])}Q{f((a[0]+b[0])/2+rng.uniform(-16,16))} '
                     f'{f((a[1]+b[1])/2+rng.uniform(-16,16))} {f(b[0])} {f(b[1])}" '
                     f'opacity=".5" stroke-width="1"/>')
    return svg(W, H, f'<g stroke="#0f0f12" stroke-width=".6" fill="none">{"".join(o)}</g>'
                     f'<g opacity=".9">{nd}</g>')

print("Work thumbnails…")
write('work-nash.svg',        gamegrid(101))
write('work-regional.svg',    netgraph(202, 44, 2))
write('work-europe.svg',      choropleth(303, 58))
write('work-covid.svg',       pointpattern(404, 620))
write('work-injuries.svg',    choropleth(505, 44))
write('work-wealth.svg',      netgraph(606, 40, 2))
write('work-north.svg',       surface(707))
write('work-quantum.svg',     surface(808))
write('work-wetland.svg',     choropleth(909, 62))

# ---- portrait backdrop: dot/network field behind the about photo
def aboutart(seed=1234):
    global W, H
    W, H = 320, 400
    rng = random.Random(seed)
    def bias(x, y):
        return max(0., 1. - (math.dist((x, y), (165, 190)) / 175) ** 1.5)
    d, pts = scatter(random.Random(seed+2), W, H, 700, .5, 2.3, .6, bias)
    core = [p for p in pts if math.dist(p, (165, 185)) < 145]
    r2 = random.Random(seed+9)
    hubs = r2.sample(core, min(28, len(core)))
    return svg(W, H, d + network(r2, hubs, k=2, stroke=.6, op=.45, rmin=2.0, rmax=5.4))
write('about.svg', aboutart())
