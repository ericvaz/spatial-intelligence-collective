#!/usr/bin/env python3
"""Refresh content/openalex.json, the dated snapshot of members' research records.

Source: OpenAlex (CC0). Each member is matched by ORCID, never by name, so
namesakes are not pulled in. Run it monthly, check the diff, then run
build_site.py. An optional OPENALEX_API_KEY environment variable raises the
daily request budget; the script works without one.

Counting policy (stated on the publications page):
  * a work counts once, however many members wrote it (deduplicated by OpenAlex
    work ID, then by DOI, then by normalized title);
  * front matter, whole proceedings volumes and stub records without DOI or venue are dropped;
  * headline totals include articles, reviews, books, book chapters and
    conference papers; preprints, editorials, errata and other items are left out;
  * a multi-fellow work has two or more members among its authors;
  * no h-index is computed for the Collective and no per-member counts are published.
"""
import json, os, re, sys, time, datetime, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
PEOPLE = json.load(open(os.path.join(ROOT, 'content', 'people.json')))['people']
KEY = os.environ.get('OPENALEX_API_KEY', '')
COUNTED = {'article', 'review', 'book', 'book-chapter', 'conference-paper'}
FIELDS = 'id,doi,title,publication_year,type,cited_by_count,authorships,primary_location'


def get(url):
    if KEY:
        url += '&api_key=' + KEY
    for i in range(5):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            err = e
            time.sleep(2 + 3 * i)
    sys.exit(f'OpenAlex request failed: {url}\n{err}')


def works_for(orcid):
    out, page = [], 1
    while True:
        d = get(f'https://api.openalex.org/works?filter=author.orcid:{orcid}'
                f'&per-page=200&page={page}&select={FIELDS}')
        out += d['results']
        if len(d['results']) < 200:
            return out
        page += 1
        time.sleep(0.2)


def norm(t):
    return re.sub(r'[^a-z0-9]', '', (t or '').lower())[:90]


def venue(w):
    src = ((w.get('primary_location') or {}).get('source') or {})
    return src.get('display_name') or ''


members = [p for p in PEOPLE if p.get('orcid')]
works, owners, author_ids = {}, {}, {}
for p in members:
    ws = works_for(p['orcid'])
    ids = set()
    for w in ws:
        works[w['id']] = w
        owners.setdefault(w['id'], set()).add(p['id'])
        for a in w.get('authorships') or []:
            au = a.get('author') or {}
            if (au.get('orcid') or '').endswith(p['orcid']) and au.get('id'):
                ids.add(au['id'].rsplit('/', 1)[-1])
    author_ids[p['id']] = sorted(ids)
    print(f"  {p['name']:28s} {len(ws):5d} works", file=sys.stderr)

# deduplicate: by work ID already; then fold DOI and title twins together
groups = {}
for wid, w in works.items():
    k = (w.get('doi') or '').lower() or norm(w.get('title'))
    if not k:
        continue
    g = groups.setdefault(k, {'w': w, 'owners': set()})
    g['owners'] |= owners[wid]
    # keep the version of record: prefer a counted type, then the most cited
    better = (w['type'] in COUNTED, w.get('cited_by_count') or 0)
    have = (g['w']['type'] in COUNTED, g['w'].get('cited_by_count') or 0)
    if better > have:
        g['w'] = w
by_title = {}
for g in groups.values():
    t = norm(g['w'].get('title'))
    if t in by_title:
        h = by_title[t]
        h['owners'] |= g['owners']
        if (g['w']['type'] in COUNTED, g['w'].get('cited_by_count') or 0) > \
           (h['w']['type'] in COUNTED, h['w'].get('cited_by_count') or 0):
            h['w'] = g['w']
    else:
        by_title[t] = g
distinct = list(by_title.values())

# front matter and whole proceedings volumes are indexed as "articles" too
FRONT = re.compile(r'^(preface|foreword|introduction|editorial|front matter|contents|index)\.?$'
                   r'|^(isprs annals|the international archives|international archives) of the photogrammetry', re.I)


def is_work(w):
    t = (w.get('title') or '').strip()
    if not t or FRONT.search(t):
        return False
    return bool(w.get('doi') or venue(w))   # no DOI and no venue: usually a stub record


counted = [g for g in distinct if g['w']['type'] in COUNTED and is_work(g['w'])]

multi = []
for g in counted:
    if len(g['owners']) >= 2:
        w = g['w']
        multi.append({
            'title': w.get('title') or '',
            'year': w.get('publication_year'),
            'type': w['type'],
            'venue': venue(w),
            'doi': w.get('doi') or '',
            'openalex': w['id'].rsplit('/', 1)[-1],
            'members': sorted(g['owners']),
        })
multi.sort(key=lambda m: (-(m['year'] or 0), m['title'].lower()))

# DOIs for the founding director's curated record (matched on title)
director = {}
for g in distinct:
    if 'eric-vaz' in g['owners'] and g['w'].get('doi'):
        director[norm(g['w'].get('title'))] = g['w']['doi']

snap = {
    'source': 'OpenAlex',
    'updated': datetime.date.today().isoformat(),
    'policy': 'Matched by ORCID. Works deduplicated by OpenAlex ID, DOI and title. '
              'Counts include articles, reviews, books, book chapters and conference papers.',
    'members_indexed': [p['id'] for p in members],
    'author_ids': author_ids,
    'totals': {
        'publications': len(counted),
        'citations': sum(g['w'].get('cited_by_count') or 0 for g in counted),
        'multi_fellow': len(multi),
    },
    'multi_fellow': multi,
    'director_dois': director,
}
out = os.path.join(ROOT, 'content', 'openalex.json')
json.dump(snap, open(out, 'w'), ensure_ascii=False, indent=1)
t = snap['totals']
print(f"content/openalex.json: {t['publications']} publications, {t['citations']} citations, "
      f"{t['multi_fellow']} multi-fellow works, {len(members)} members indexed", file=sys.stderr)
