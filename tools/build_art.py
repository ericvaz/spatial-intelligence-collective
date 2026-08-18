#!/usr/bin/env python3
import math, random, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from genart import *

print("Generating artwork…")

# ============================================================ HERO
def hero():
    W, H = 900, 620
    body = fade('hf', '.56', '.46', '.74')
    inner = []
    # dense topographic base - the dominant texture
    lv = [round(-.85 + i*.085, 3) for i in range(28)]
    inner.append(contours(random.Random(7), W, H, lv, stroke=.6, op=.42, n=17,
                          smin=.11, smax=.30))
    # perspective mesh, lower-right quadrant
    inner.append(mesh(W, H, 405, 292, 20.5, 15, 24, 21, skew=-.15, stroke=.42, op=.3))
    # particle field, biased to a soft landmass in the centre-right
    def bias(x, y):
        d1 = math.dist((x, y), (505, 285)) / 330
        d2 = math.dist((x, y), (660, 415)) / 260
        return max(0., 1. - min(d1, d2) ** 1.6)
    dots, pts = scatter(random.Random(11), W, H, 1150, .5, 2.3, .62, bias)
    inner.append(dots)
    # clustered hub network
    rng2 = random.Random(3)
    core = [p for p in pts if math.dist(p, (520, 320)) < 315]
    hubs = rng2.sample(core, min(46, len(core)))
    inner.append(network(rng2, hubs, k=2, stroke=.62, op=.5, rmin=2.3, rmax=6.6))
    body += '<g mask="url(#mhf)">' + ''.join(inner) + '</g>'
    return svg(W, H, body)
write('hero.svg', hero())

# ============================================================ RESEARCH AREAS (5)
AW, AH = 300, 150

def a_geocomputation():
    """Stacked ridgelines - computational surfaces."""
    rng = random.Random(42); o = []
    for k in range(16):
        y0 = 22 + k * 8.0
        pts = []
        ph = rng.uniform(0, 6.3)
        for i in range(101):
            x = i * AW / 100
            t = x / AW
            env = math.exp(-((t - .5) ** 2) / .12)
            y = y0 - env * (26 * math.sin(t * 7 + ph) + 13 * math.sin(t * 13 + ph * 2)) * (1 - k / 22)
            pts.append((x, y))
        o.append(f'<path d="{path(pts)}"/>')
    return svg(AW, AH, f'<g stroke="#0f0f12" stroke-width=".7" opacity=".5" '
                       f'stroke-linecap="round">{"".join(o)}</g>')
write('area-geocomputation.svg', a_geocomputation())

def a_spatial():
    """Dot-density field - point pattern / spatial statistics."""
    rng = random.Random(5)
    cl = [(rng.uniform(40, 260), rng.uniform(30, 120), rng.uniform(18, 46)) for _ in range(7)]
    def bias(x, y):
        return min(1., .1 + sum(math.exp(-math.dist((x, y), (cx, cy)) ** 2 / (2 * s * s))
                                for cx, cy, s in cl))
    d, _ = scatter(random.Random(9), AW, AH, 620, .5, 2.4, .78, bias)
    return svg(AW, AH, d)
write('area-spatial.svg', a_spatial())

def a_geoai():
    """Layered node-link graph - neural / machine learning."""
    rng = random.Random(77)
    layers, nodes = [4, 6, 6, 4], []
    for li, n in enumerate(layers):
        x = 42 + li * 72
        col = [(x + rng.uniform(-9, 9), AH / 2 + (i - (n - 1) / 2) * 22 + rng.uniform(-6, 6))
               for i in range(n)]
        nodes.append(col)
    ed = []
    for a, b in zip(nodes, nodes[1:]):
        for p in a:
            for q in b:
                if rng.random() < .55:
                    ed.append(f'<line x1="{f(p[0])}" y1="{f(p[1])}" x2="{f(q[0])}" y2="{f(q[1])}" '
                              f'opacity="{f(.16 + .4*rng.random())}"/>')
    nd = ''
    for col in nodes:
        for x, y in col:
            r = 2.4 + 3.4 * rng.random() ** 1.5
            g = int(10 + 90 * rng.random())
            nd += f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="rgb({g},{g},{g})"/>'
    return svg(AW, AH, f'<g stroke="#0f0f12" stroke-width=".6">{"".join(ed)}</g>{nd}')
write('area-geoai.svg', a_geoai())

def a_complexity():
    """Radial small-world network - emergence, adaptive systems."""
    rng = random.Random(31)
    cx, cy = AW / 2, AH / 2
    nodes = [(cx, cy)]
    for ring, (n, r) in enumerate([(9, 30), (14, 52), (18, 70)]):
        for i in range(n):
            a = i * 2 * math.pi / n + ring * .3
            nodes.append((cx + math.cos(a) * r * 1.55 + rng.uniform(-4, 4),
                          cy + math.sin(a) * r * .92 + rng.uniform(-4, 4)))
    ed = []
    for i, a in enumerate(nodes):
        for j, b in enumerate(nodes):
            if j <= i: continue
            d = math.dist(a, b)
            if d < 34 or rng.random() < .012:      # local links + rare long-range
                ed.append(f'<line x1="{f(a[0])}" y1="{f(a[1])}" x2="{f(b[0])}" y2="{f(b[1])}" '
                          f'opacity="{f(max(.1, .5 - d/300))}"/>')
    nd = ''
    for i, (x, y) in enumerate(nodes):
        r = 4.6 if i == 0 else 1.8 + 3.0 * rng.random() ** 1.6
        nd += f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="#141418"/>'
    return svg(AW, AH, f'<g stroke="#0f0f12" stroke-width=".6">{"".join(ed)}</g>'
                       f'<g opacity=".9">{nd}</g>')
write('area-complexity.svg', a_complexity())

def a_quantum():
    """Orbital / superposition - quantum computing."""
    rng = random.Random(88)
    cx, cy = AW / 2, AH / 2
    o = []
    for i, rot in enumerate([0, 60, 120]):
        o.append(f'<ellipse cx="{cx}" cy="{cy}" rx="74" ry="26" '
                 f'transform="rotate({rot} {cx} {cy})" stroke="#0f0f12" '
                 f'stroke-width=".8" opacity=".55"/>')
    # probability cloud
    for _ in range(190):
        a = rng.uniform(0, 6.3); rr = abs(rng.gauss(0, 1)) * 30
        x, y = cx + math.cos(a) * rr * 1.9, cy + math.sin(a) * rr * .85
        o.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(.5 + rng.random()*1.1)}" '
                 f'fill="#26262c" opacity="{f(.2 + .5*rng.random())}"/>')
    # electrons on orbits
    for i, (rot, t) in enumerate([(0, .18), (60, .62), (120, .87)]):
        a = t * 2 * math.pi
        x, y = 74 * math.cos(a), 26 * math.sin(a)
        rr = math.radians(rot)
        xx = cx + x * math.cos(rr) - y * math.sin(rr)
        yy = cy + x * math.sin(rr) + y * math.cos(rr)
        o.append(f'<circle cx="{f(xx)}" cy="{f(yy)}" r="3.4" fill="#0f0f12"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="6.5" fill="#0f0f12"/>')
    return svg(AW, AH, ''.join(o))
write('area-quantum.svg', a_quantum())
