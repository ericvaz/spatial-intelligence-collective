# Spatial Intelligence Collective — Complexity Spatial Analysis

Site of the Spatial Intelligence Collective, led by **Eric Vaz**, Full Professor, Department of Geography &
Environmental Studies, Toronto Metropolitan University.

**Live:** https://ericvaz.github.io/spatial-intelligence-collective/

Geocomputation · GeoAI · Complexity Science · Quantum Computing

## Contents

- `index.html`: home page with research, selected work, people, STRANGE, news, data, and contact
- `publications/`: the full curated record (80 entries) with theme filters and search
- `assets/css/site.css`: the single stylesheet for both pages (Inter, near-black on white, phone first)
- `assets/strange/`: the STRANGE wordmark (SVG) and issue covers
- `assets/covers/`: Springer cover images for the seven monographs and edited volumes
- `tools/`: the build scripts

## STRANGE

STRANGE is the Collective's magazine. The current issue sits in the `#strange` section of
`index.html`. When a new issue is ready, export its cover from Figma, save it as
`assets/strange/strange-NN.webp` (about 900 px wide) plus a `-sm` version (600 px), point the
featured `<figure class="issue">` at it, and move the previous issue into the `<ul class="archive">`
list just below (newest first). The archive grid stays hidden while it is empty.

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
