# Eric Vaz Lab — Complexity Spatial Analysis

Lab site for the research of **Eric Vaz**, Full Professor, Department of Geography &
Environmental Studies, Toronto Metropolitan University.

**Live:** https://ericvaz.github.io/ericvazlab/

Geocomputation · GeoAI · Complexity Science · Quantum Computing

## Contents

- `index.html` — lab home: research areas, selected work, people, the lab, news, contact
- `publications/` — the full curated record (80 entries) with theme filters and search
- `assets/art/` — generative grayscale artwork, produced deterministically by `tools/`
- `assets/js/hero-ca.js` — the live hero: a Larger-than-Life cellular automaton
  whose field drives the contours, particle cloud and node-link graph
- `assets/covers/` — Springer cover images for the seven monographs and edited volumes
- `tools/` — the build scripts

Only published work appears on the site. Anything under review or in preparation is
deliberately excluded.

## Content provenance

Every publication, book and biographical claim on this site comes from the
existing record: the JSON-LD on ericvaz.com, Google Scholar, and Springer. Nothing is
invented. Citation metrics (3,843 citations, h-index 32) are as reported by Google
Scholar and should be refreshed periodically.

## Rebuilding

The artwork and the publications page are generated. Requires Python 3 only — no
dependencies, no build toolchain.

```bash
python3 tools/build_art.py     # hero + research-area artwork
python3 tools/build_work.py    # selected-work thumbnails + about backdrop
python3 tools/build_pubs.py    # publications/index.html from tools/pubs.json
```

All generators are seeded, so rebuilds are byte-identical unless the source data changes.
To add a publication, edit `tools/pubs.json` (or the `EXTRA` list in `tools/build_pubs.py`
for items not yet in the JSON-LD record) and re-run `build_pubs.py`.

## Local preview

```bash
python3 -m http.server 8000
```

## Custom domain

To serve at `ericvazlab.ca`, add a `CNAME` file containing the bare domain, then point
DNS at GitHub Pages (four `A` records for the apex, or a `CNAME` record to
`ericvaz.github.io` for a subdomain). Do this only once DNS is configured — an
unresolved `CNAME` file takes the `github.io` URL offline.

## The hero animation

The hero is not a video or a static image. A Larger-than-Life cellular automaton runs on
a lattice: each cell reads the mean state of an isotropic gaussian neighbourhood and
grows when that mean lands inside a narrow band, otherwise it decays. Everything drawn is
read back out of that one field — iso-contours by marching squares, a particle cloud from
cells above threshold, and a node-link graph over separated local maxima. A small panel
in the corner prints the rule actually being evaluated, with live counters.

**It stops.** The legible state of this system is a transient, not an attractor: measured
over 260 steps the field's high-frequency energy climbs from 0.026 to 0.112, so a run
left going drifts from clean structure into noise. Adding a diffusion term to damp that
kills the system instead (alive fraction falls to zero by step 250). The lifecycle is
therefore budgeted in steps rather than seconds — 25 warm-up plus 60 live, landing inside
the band where the field reads clean — after which it eases down and halts.

**Click to feed.** A click drops sugar: an attractant that diffuses into a gradient,
widens the growth band along it so structures bulge toward the drop, and is consumed on
arrival. Measured on the real rule, mass inside the drop radius rises 154% over 70 steps
while a control region is unchanged, and 82% of the sugar is eaten. Each drop buys a
bounded number of extra steps and applies one relaxation pass first, so repeated feeding
does not accumulate into noise.

**Steadiness.** Three things damp the flicker a raw CA would produce: rendering reads an
exponential moving average of the state rather than the state itself; graph nodes persist
across frames, matched to maxima and eased toward new positions with a life value fading
them in and out; and edges use hysteresis, forming at a shorter distance than they break.

Rendering is batched into a handful of canvas fills per frame, capped near 25fps, and
paused off-screen. Visitors who prefer reduced motion, or whose browser lacks canvas, get
the static SVG instead.
