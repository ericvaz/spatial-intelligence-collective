#!/usr/bin/env python3
"""Placeholder identity tiles — a seeded node-link cluster per person.
Swap for real headshots when they are available."""
import math, random, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from genart import *

W, H = 300, 300

def tile(name, seed):
    rng = random.Random(seed)
    cx, cy = W/2, H*.46
    def bias(x, y):
        return max(0., 1. - (math.dist((x, y), (cx, cy)) / 118) ** 1.5)
    dots, pts = scatter(random.Random(seed+3), W, H, 340, .5, 2.1, .5, bias)
    core = [p for p in pts if math.dist(p, (cx, cy)) < 96]
    r2 = random.Random(seed+7)
    hubs = r2.sample(core, min(17, len(core)))
    net = network(r2, hubs, k=2, stroke=.6, op=.42, rmin=2.0, rmax=5.0)
    return svg(W, H, dots + net)

print("People tiles…")
for slug, seed in [('eric-vaz', 4101), ('teagan-soni', 4102), ('anastasiia-smirnova', 4103)]:
    write(f'person-{slug}.svg', tile(slug, seed))
