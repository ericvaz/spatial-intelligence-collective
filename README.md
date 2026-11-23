# Spatial Intelligence Collective

Site of the Spatial Intelligence Collective, a research network founded and led by Eric Vaz,
Full Professor, Department of Geography and Environmental Studies, Toronto Metropolitan University.

**Live:** https://spatialintelligence.network/

## Pages

- `index.html`: home page with research, recent joint work, people, STRANGE, books, news, data, and contact
- `people/`: the full directory, with each member's Google Scholar, ORCID and OpenAlex links
- `publications/`: the research record of all members, the works written by two or more fellows, and Eric Vaz's curated record
- `learn/`: the SIC Lab (open data and browser spatial statistics, repo ericvaz/sic-lab, served at lab.spatialintelligence.network) and its tutorials
- `strange/`: the magazine, its masthead, and how to contribute

## Content

Everything that changes as the Collective grows lives in `content/`:

- `people.json`: every member, their position, institution, country, STRANGE role and profile identifiers
- `openalex.json`: the dated research snapshot (generated, do not edit by hand)
- `director.json`: Eric Vaz's curated publication record and Springer volumes, with DOIs

## Adding a fellow

1. Add an entry to `content/people.json` (keep `sort` as the surname used for ordering, set `strange` to `"board"` for editorial board members).
2. Run `python3 tools/fetch_openalex.py` if the fellow has an ORCID, then `python3 tools/build_site.py`.
3. Check the diff and push.

The builder fills the marked `<!--b:...-->` regions of `index.html` and writes the other pages,
`sitemap.xml` and `robots.txt`, so counts of fellows, universities, countries and the masthead
are always derived from `people.json`. Edit anything outside the marked regions by hand.

## Research record

`tools/fetch_openalex.py` matches each member to OpenAlex by ORCID, deduplicates works by OpenAlex
ID, DOI and title, and counts articles, reviews, books, chapters and conference papers. Run it once
a month.
No per-member counts or collective h-index are published.

## STRANGE

When a new issue is ready, export its cover from Figma, save it as `assets/strange/strange-NN.webp`
(about 900 px wide) plus a `-sm` version (600 px), and update the cover in `tools/build_site.py`
and `index.html`. Give each issue its own page at `strange/issue-NN/` and list it in the archive.

## Rebuilding the artwork

```bash
python3 tools/build_art.py     # hero and research-area artwork
python3 tools/build_work.py    # work thumbnails and about backdrop
```

## Local preview

```bash
python3 -m http.server 8000
```
