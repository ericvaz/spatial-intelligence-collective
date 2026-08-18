# Eric Vaz Lab — Complexity Spatial Analysis

Lab site for the research of **Eric Vaz**, Full Professor, Department of Geography &
Environmental Studies, Toronto Metropolitan University.

**Live:** https://ericvaz.github.io/ericvazlab/

Geocomputation · GeoAI · Complexity Science · Quantum Computing

## Contents

- `index.html` — lab home: research areas, selected work, people, the lab, news, contact
- `publications/` — the full curated record (80 entries) with theme filters and search
- `assets/art/` — generative grayscale artwork, produced deterministically by `tools/`
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
