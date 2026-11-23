#!/usr/bin/env python3
"""Build the Spatial Intelligence Collective site from the files in content/.

  content/people.json    every member, their roles and profile links (edit by hand)
  content/openalex.json  dated research snapshot (refresh with tools/fetch_openalex.py)
  content/director.json  Eric Vaz's curated record and Springer volumes

Writes people/, strange/, publications/, sitemap.xml and robots.txt, and fills
the marked <!--b:...--> regions of index.html, so the counts, people lists and
masthead are always derived from one source. Python 3 only, no dependencies.
"""
import json, os, re, sys, html, datetime, urllib.parse
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
SITE = 'https://spatialintelligence.network'
CSS_V = 11


def load(name):
    return json.load(open(os.path.join(ROOT, 'content', name)))


PD = load('people.json')
PEOPLE, META = PD['people'], PD['meta']
OA = load('openalex.json')
DIR = load('director.json')
BY_ID = {p['id']: p for p in PEOPLE}
esc = lambda s: html.escape(str(s or ''), quote=True)

# ------------------------------------------------------------------ checks
REQ = ('id', 'name', 'sort', 'category', 'position', 'institution', 'country')
ids = [p['id'] for p in PEOPLE]
dup = [i for i, c in Counter(ids).items() if c > 1]
if dup:
    sys.exit(f'duplicate ids in people.json: {dup}')
for p in PEOPLE:
    miss = [k for k in REQ if not p.get(k)]
    if miss:
        sys.exit(f'{p.get("id")}: missing {miss}')
    if p['category'] not in ('lead', 'fellow', 'honorary', 'advisory', 'doctoral'):
        sys.exit(f'{p["id"]}: unknown category {p["category"]}')
for m in OA['multi_fellow']:
    for i in m['members']:
        if i not in BY_ID:
            sys.exit(f'openalex.json names unknown member {i}; rerun fetch_openalex.py')

# ------------------------------------------------------------------ derived facts
az = lambda ps: sorted(ps, key=lambda p: p['sort'].lower())
lead = [p for p in PEOPLE if p['category'] == 'lead']
fellows = az([p for p in PEOPLE if p['category'] in ('fellow', 'honorary', 'advisory')])
honorary = [p for p in fellows if p['category'] == 'honorary']
advisory = [p for p in fellows if p['category'] == 'advisory']
doctoral = [p for p in PEOPLE if p['category'] == 'doctoral']
academics = lead + fellows
N_FELLOWS = len(fellows)
N_UNIS = len({p['institution'] for p in academics})
N_COUNTRIES = len({p['country'] for p in academics})
N_DISC = META['disciplines']
board = az([p for p in PEOPLE if p.get('strange') == 'board'])
director_p = [p for p in PEOPLE if p.get('strange') == 'director']
manager_p = [p for p in PEOPLE if p.get('strange') == 'manager']
N_MAST = len(director_p) + len(manager_p) + len(board)
T = OA['totals']
indexed = len(OA['members_indexed'])
N_IDX_FELLOWS = sum(1 for p in fellows if p['id'] in OA['members_indexed'])
COVER = ('All ' if N_IDX_FELLOWS == len(fellows) else f'{N_IDX_FELLOWS} of ') + f'{len(fellows)} fellows and the director indexed'
UPDATED = datetime.date.fromisoformat(OA['updated'])
UPDATED_TXT = f'{UPDATED.day} {UPDATED:%B %Y}'
fmt = lambda n: f'{n:,}'


def nav(depth, here=''):
    up = '../' * depth
    items = [('Research', f'{up}#research', ''), ('People', f'{up}people/', 'people'),
             ('STRANGE', f'{up}strange/', 'strange'), ('Publications', f'{up}publications/', 'publications'),
             ('Learn', f'{up}learn/', 'learn'),
             ('Contact', f'{up}#contact', '')]
    return '\n      '.join(
        f'<a href="{h}"' + (' aria-current="page"' if k and k == here else '') + f'>{t}</a>'
        for t, h, k in items)


ICON = ("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><circle cx='16' cy='16' r='4' fill='%23111'/>"
        "<circle cx='6' cy='7' r='2' fill='%23111'/><circle cx='26' cy='9' r='2' fill='%23111'/><circle cx='8' cy='26' r='2' fill='%23111'/>"
        "<circle cx='25' cy='25' r='2' fill='%23111'/><g stroke='%23111' stroke-width='1' fill='none'><path d='M16 16 6 7M16 16l10-7M16 16 8 26M16 16l9 9'/></g></svg>")


def page(path, title, desc, body, here, script='', jsonld=None, og_image='assets/art/og-sic.jpg'):
    depth = path.count('/')
    up = '../' * depth
    url = f'{SITE}/{path}'
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>\n' if jsonld else ''
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/{og_image}">
<meta name="theme-color" content="#ffffff">
<link rel="preload" href="{up}assets/fonts/inter-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{up}assets/css/site.css?v={CSS_V}">
<link rel="icon" href="{ICON}">
{ld}</head>
<body>
<a class="skip" href="#main">Skip to content</a>

<header class="hdr">
  <div class="wrap">
    <a class="brand" href="{up or './'}">Spatial Intelligence Collective</a>
    <button class="menu" aria-expanded="false" aria-controls="nav">Menu</button>
    <nav class="nav" id="nav" aria-label="Main">
      {nav(depth, here)}
    </nav>
  </div>
</header>

<main id="main">
{body}
</main>

<footer class="ftr">
  <div class="wrap">
    <span>© <span id="yr">2026</span> Spatial Intelligence Collective · Toronto Metropolitan University</span>
    <span><a href="{up}people/">People</a> · <a href="{up}publications/">Publications</a> · <a href="{up}learn/">Learn</a> · <a href="{up}strange/">STRANGE</a> · <a href="{up}#flows">Everything flows</a></span>
  </div>
</footer>

<script>
document.getElementById('yr').textContent = new Date().getFullYear();
var m=document.querySelector('.menu'), nv=document.getElementById('nav'), h=document.querySelector('.hdr');
m.addEventListener('click',function(){{var o=nv.classList.toggle('open');m.setAttribute('aria-expanded',o);m.textContent=o?'Close':'Menu';}});
window.addEventListener('scroll',function(){{h.classList.toggle('scrolled',window.scrollY>8);}},{{passive:true}});
{script}</script>
</body>
</html>
"""


def write(rel, text):
    out = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w').write(text)


def links(p, cls='plinks'):
    out = []
    if p.get('scholar'):
        out.append(f'<a href="https://scholar.google.com/citations?user={esc(p["scholar"])}" target="_blank" rel="noopener">Google Scholar</a>')
    if p.get('orcid'):
        out.append(f'<a href="https://orcid.org/{esc(p["orcid"])}" target="_blank" rel="noopener">ORCID</a>')
    if p.get('openalex'):
        out.append(f'<a href="https://openalex.org/authors/{esc(p["openalex"][0])}" target="_blank" rel="noopener">OpenAlex</a>')
    return f'<span class="{cls}">' + ' · '.join(out) + '</span>' if out else ''


def affil(p):
    if p['category'] == 'honorary':
        return f'Honorary fellow · {esc(p["position"])} · {esc(p["institution"])}'
    if p['category'] == 'advisory':
        return f'Advisory board · {esc(p["position"])} · {esc(p["institution"])}'
    if p['category'] == 'doctoral':
        return f'{esc(p["position"])}, {esc(p["institution"])}'
    if p['category'] == 'lead':
        return f'{esc(p["position"])}, {esc(p["institution"])}'
    return f'{esc(p["position"])} · {esc(p["institution"])}'


def person_ld(p):
    same = []
    if p.get('orcid'):
        same.append(f'https://orcid.org/{p["orcid"]}')
    if p.get('scholar'):
        same.append(f'https://scholar.google.com/citations?user={p["scholar"]}')
    d = {'@type': 'Person', 'name': p['name'], 'jobTitle': p['position'],
         'affiliation': {'@type': 'CollegeOrUniversity', 'name': p['institution']},
         'url': f'{SITE}/people/#{p["id"]}'}
    if same:
        d['sameAs'] = same
    return d


# ================================================================== people/
def entry(p, bio=True):
    tag = ' <span class="tag">STRANGE board</span>' if p.get('strange') == 'board' else ''
    extra = ''
    if bio and p.get('bio'):
        extra = f'<p class="d">{p["bio"]}</p>'
    elif p.get('research'):
        extra = f'<p class="d">{esc(p["research"])}</p>'
    return (f'<li id="{p["id"]}"><span class="n">{esc(p["name"])}{tag}</span>'
            f'<span class="a">{affil(p)}</span>{extra}{links(p)}</li>')


people_body = f"""<section class="page-head">
  <div class="wrap">
    <h1>People</h1>
    <p class="lede">The Spatial Intelligence Collective is a research network founded and led by Eric Vaz at Toronto Metropolitan University. Its fellows hold appointments at their own universities and work across geography, planning, geomatics engineering, remote sensing, information management, computing science, business, economics, and nursing. Fellowship is by invitation.</p>
    <ul class="metrics"><li><b>{N_FELLOWS}</b> fellows</li><li><b>{N_UNIS}</b> universities</li><li><b>{N_COUNTRIES}</b> countries</li><li><b>{N_DISC}</b> disciplines</li></ul>
  </div>
</section>

<section id="lead">
  <div class="wrap">
    <p class="label">Lead</p>
    <ul class="people">{''.join(entry(p) for p in lead)}</ul>
  </div>
</section>

<section id="honorary">
  <div class="wrap">
    <p class="label">Honorary fellows</p>
    <ul class="people">{''.join(entry(p) for p in honorary)}</ul>
  </div>
</section>

{f'''<section id="advisory">
  <div class="wrap">
    <p class="label">Advisory board</p>
    <ul class="people">{''.join(entry(p) for p in advisory)}</ul>
  </div>
</section>

''' if advisory else ''}<section id="fellows">
  <div class="wrap">
    <p class="label">Fellows · {N_FELLOWS - len(honorary) - len(advisory)}</p>
    <ul class="people cols">{''.join(entry(p) for p in fellows if p['category'] == 'fellow')}</ul>
  </div>
</section>

<section id="doctoral">
  <div class="wrap">
    <p class="label">Doctoral researchers · {len(doctoral)}</p>
    <ul class="people cols">{''.join(entry(p) for p in doctoral)}</ul>
    <p class="more">Researchers whose work fits the Collective are welcome to <a href="mailto:evaz@torontomu.ca?subject=Spatial%20Intelligence%20Collective">write to Eric Vaz</a>. Each fellow's own research record is linked from their entry, and the <a href="../publications/">publications page</a> brings the Collective's work together.</p>
  </div>
</section>"""

people_ld = {'@context': 'https://schema.org', '@type': 'ItemList', 'name': 'Members of the Spatial Intelligence Collective',
             'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'item': person_ld(p)}
                                 for i, p in enumerate(lead + fellows + doctoral)]}
write('people/index.html', page(
    'people/', 'People · Spatial Intelligence Collective',
    f'The {N_FELLOWS} fellows, lead and doctoral researchers of the Spatial Intelligence Collective, at {N_UNIS} universities in {N_COUNTRIES} countries.',
    people_body, 'people', jsonld=people_ld))

# ================================================================== strange/
mast = ''.join(f'<li><span class="n">{esc(p["name"])}</span><span class="a">Director</span></li>' for p in director_p)
mast += ''.join(f'<li><span class="n">{esc(p["name"])}</span><span class="a">Editorial manager</span></li>' for p in manager_p)
board_li = ''.join(f'<li><span class="n"><a href="../people/#{p["id"]}">{esc(p["name"])}</a></span><span class="a">{affil(p)}</span></li>' for p in board)
strange_body = f"""<div class="strange-band strange-page">
  <div class="wrap">
    <div class="strange">
      <div class="s-head">
        <p class="label">The Collective's magazine</p>
        <h1><img class="wordmark" src="../assets/strange/wordmark.svg" alt="STRANGE" width="300" height="51"></h1>
        <p class="tagline">Space, place, and imagination.</p>
      </div>
      <figure class="issue">
        <img src="../assets/strange/strange-01.webp" srcset="../assets/strange/strange-01-sm.webp 600w, ../assets/strange/strange-01.webp 900w" sizes="(min-width:760px) 420px, 72vw" width="900" height="1201" alt="Cover of STRANGE Issue 01: a flooded classical hall with arches and a staircase descending into still water.">
        <figcaption><b>Issue 01</b> <span class="status">Winter issue · In preparation</span></figcaption>
      </figure>
      <div class="s-body">
        <p class="lede">STRANGE explores space, place, and imagination through essays, images, letters, and conversations. It welcomes short reflections as well as longer contributions, and it gives the stranger problems of spatial analysis a place to be thought through in public.</p>
        <p class="note">STRANGE is an editorially curated magazine published by the Spatial Intelligence Collective.</p>
      </div>
    </div>
  </div>
</div>

<section id="masthead">
  <div class="wrap">
    <p class="label">Masthead · {N_MAST}</p>
    <ul class="people">{mast}</ul>
    <h2 class="sub">Editorial board</h2>
    <ul class="people cols">{board_li}</ul>
    <p class="note">Further board members to be announced.</p>
  </div>
</section>

<section id="submit">
  <div class="wrap">
    <p class="label">Contributing</p>
    <h2>Write for STRANGE.</h2>
    <p class="lede muted">Submission guidelines and a submission form will be published here before Issue 01 appears. Until then, contributors can <a href="mailto:evaz@torontomu.ca?subject=STRANGE%20contribution">write to the editors</a> with a short description of their idea.</p>
  </div>
</section>

<section id="issues">
  <div class="wrap">
    <p class="label">Issues</p>
    <!-- When Issue 01 is published, give it a page at strange/issue-01/ and list it here, newest first:
         <li><a href="issue-01/"><img src="../assets/strange/strange-01-sm.webp" alt="STRANGE Issue 01 cover">Issue 01 · Winter 2027</a></li> -->
    <ul class="archive"></ul>
    <p class="muted">Issue 01 is in preparation.</p>
  </div>
</section>"""
strange_ld = {'@context': 'https://schema.org', '@type': 'Periodical', 'name': 'STRANGE',
              'description': 'The magazine of the Spatial Intelligence Collective: space, place, and imagination.',
              'url': f'{SITE}/strange/', 'image': f'{SITE}/assets/strange/strange-01.webp',
              'publisher': {'@type': 'Organization', 'name': 'Spatial Intelligence Collective', 'url': f'{SITE}/'},
              'editor': {'@type': 'Person', 'name': director_p[0]['name']} if director_p else None}
write('strange/index.html', page(
    'strange/', 'STRANGE · Spatial Intelligence Collective',
    'STRANGE is the magazine of the Spatial Intelligence Collective: essays, images, letters, and conversations on space, place, and imagination.',
    strange_body, 'strange', jsonld=strange_ld, og_image='assets/strange/strange-01.webp'))

# ================================================================== publications/
THEMES = [
    ("quantum", "Quantum", r"quantum"),
    ("complexity", "Complexity", r"nash|equilibri|network|cluster structur|resilien|emergen|graph theory|complex|innovation support|gravit|multi-criteria|biplot"),
    ("geoai", "GeoAI & ML", r"machine learning|artificial intelligence|neural|deep learn|random forest|big data|self-organi|crowdsourc|volunteered|citizen sci|collaborative mapping"),
    ("geocomp", "Geocomputation", r"cellular automata|agent-based|simulat|markov|predicting urban growth|forecast|scenario|model"),
    ("spatial", "Spatial Analysis", r"spatial|geovisual|landscape metric|hedonic|dasymetric|autocorrelation|mapping|geographic information|gis|remote sens|earth observation|land cover|land use|geoinformation|coastal|vulnerab"),
    ("regional", "Regional & Urban", r"."),
]


def theme(t):
    t = t.lower()
    for k, _, pat in THEMES:
        if re.search(pat, t):
            return k
    return 'regional'


def title_link(title, doi):
    href = doi or 'https://scholar.google.com/scholar?q=' + urllib.parse.quote(f'"{title}"')
    return f'<a href="{esc(href)}" target="_blank" rel="noopener">{esc(title)}</a>'


TYPE = {'article': 'Article', 'review': 'Review', 'book': 'Book', 'book-chapter': 'Chapter', 'conference-paper': 'Conference paper'}
together = []
for w in OA['multi_fellow']:
    names = ', '.join(f'<a href="../people/#{i}">{esc(BY_ID[i]["name"])}</a>' for i in w['members'])
    v = esc(w['venue'])
    together.append(
        f'<article class="pub" data-m="{" ".join(w["members"])}" data-t="{theme(w["title"] + " " + w["venue"])}">'
        f'<div class="y">{w["year"] or ""}</div><div>'
        f'<div class="t">{title_link(w["title"], w["doi"])}</div>'
        f'<div class="a">{TYPE.get(w["type"], "Work")}{" · " + v if v else ""}</div>'
        f'<div class="a fellows">{names}</div></div></article>')
in_multi = Counter(i for w in OA['multi_fellow'] for i in w['members'])
opts = ''.join(f'<option value="{p["id"]}">{esc(p["name"])}</option>'
               for p in az(lead + fellows) if in_multi[p['id']])

records = ''.join(
    f'<li><span class="n"><a href="../people/#{p["id"]}">{esc(p["name"])}</a></span>'
    f'<span class="a">{esc(p["institution"])}</span>{links(p)}</li>'
    for p in lead + fellows)
not_indexed = [p for p in PEOPLE if p['id'] not in OA['members_indexed']]

drows = []
for p in sorted(DIR['publications'], key=lambda p: (-int(p['year']), p['title'])):
    au = '; '.join(p.get('authors') or [])
    ven = esc(p.get('venue') or '')
    drows.append(
        f'<article class="pub" data-t="{theme(p["title"] + " " + (p.get("venue") or ""))}">'
        f'<div class="y">{p["year"]}</div><div>'
        f'<div class="t">{title_link(p["title"], p.get("doi"))}</div>'
        f'<div class="a">{esc(au)}{" · " if au and ven else ""}<span class="v">{ven}</span></div>'
        f'</div></article>')
chips = ''.join(f'<button data-f="{k}" aria-pressed="false">{esc(l)}</button>' for k, l, _ in THEMES)
DOI_ISBN = {"978-3-032-19210-3": "978-3-032-19211-0"}
books = ''.join(
    f'<a class="book" href="https://link.springer.com/book/10.1007/{DOI_ISBN.get(b["isbn"], b["isbn"])}" target="_blank" rel="noopener">'
    f'<img src="../assets/covers/{b["isbn"]}.webp" alt="{esc(b["title"])}: {esc(b["subtitle"])}" loading="lazy">'
    f'<h3>{esc(b["title"])}</h3><span>{esc(b["subtitle"])}</span><span>{b["year"]} · Springer</span></a>'
    for b in DIR['books'])
dm = DIR['metrics']

pubs_body = f"""<section class="page-head">
  <div class="wrap">
    <h1>Publications</h1>
    <p class="lede">The research record of the Collective's members, drawn from OpenAlex and matched to each member by ORCID. Every member's own record is one click away, and the work fellows have written together is listed in full.</p>
    <ul class="metrics">
      <li><b>{fmt(T['publications'])}</b> publications by members</li>
      <li><b>{T['multi_fellow']}</b> written by two or more fellows</li>
      <li><b>{COVER}</b></li>
    </ul>
    <p class="prov">Source: OpenAlex, matched to each member by ORCID · updated {UPDATED_TXT}.</p>
    <details class="method">
      <summary>How these numbers are counted</summary>
      <p>Each member is matched to OpenAlex through their ORCID rather than by name, which keeps most namesakes out; OpenAlex can still attribute a work to the wrong person, so the figures are close estimates rather than exact counts. A work counts once however many members wrote it: duplicates are folded together by OpenAlex identifier, DOI, and title. The totals include journal articles, reviews, books, book chapters, and conference papers, and leave out preprints, editorials, errata, front matter, and whole proceedings volumes. Together these {fmt(T['publications'])} publications have been cited {fmt(T['citations'])} times in OpenAlex; one citing paper can cite several of them, so this is not a count of distinct citing works.</p>
      <p>The totals describe the work members bring to the Collective across their careers, much of it written before the Collective existed. Works by two or more fellows include collaborations from before the Collective was founded. No collective h-index is given, and no member is ranked against another; individual metrics are on each member's own profiles. The record is refreshed monthly, and members can correct or withdraw their records by writing to Eric Vaz.</p>
    </details>
  </div>
</section>

<section id="together">
  <div class="wrap">
    <p class="label">Written together · {T['multi_fellow']} works</p>
    <h2>Work by two or more fellows.</h2>
    <div class="tools">
      <label class="pick-m"><span>Fellow</span>
        <select id="mf"><option value="">All fellows</option>{opts}</select></label>
      <input class="search" id="q2" type="search" placeholder="Search titles and journals" aria-label="Search works by two or more fellows">
    </div>
    <p class="count" id="c2" aria-live="polite"></p>
    <div class="list" id="l2">{''.join(together)}</div>
    <p class="count" id="e2" hidden>No works match.</p>
  </div>
</section>

<section id="records">
  <div class="wrap">
    <p class="label">Members' records</p>
    <h2>Every member's own record.</h2>
    <ul class="people cols">{records}</ul>
    <p class="note">{' and '.join(esc(p['name']) for p in not_indexed)} {'are' if len(not_indexed) > 1 else 'is'} not yet indexed.</p>
  </div>
</section>

<section id="director">
  <div class="wrap">
    <p class="label">Founding director's record · {len(drows)} entries</p>
    <h2>Eric Vaz: selected publications.</h2>
    <ul class="metrics"><li><b>{dm['citations']}</b> citations</li><li><b>h-index</b> {dm['h_index']}</li><li><b>{len(DIR['books'])}</b> Springer volumes</li></ul>
    <p class="prov">Curated by Eric Vaz from his own record. Citation figures from {esc(dm['source'])}.</p>
    <div class="filters">
      <button data-f="all" aria-pressed="true">All</button>
      {chips}
    </div>
    <input class="search" id="q" type="search" placeholder="Search titles, authors, journals" aria-label="Search Eric Vaz's publications">
    <p class="count" id="count" aria-live="polite"></p>
    <div class="list" id="list">{''.join(drows)}</div>
    <p class="count" id="empty" hidden>No publications match that filter.</p>
  </div>
</section>

<section id="books">
  <div class="wrap">
    <p class="label">Springer volumes by Eric Vaz</p>
    <div class="books">{books}</div>
  </div>
</section>"""

pubs_js = r"""
function wire(listId, countId, emptyId, test){
  var items=[].slice.call(document.querySelectorAll('#'+listId+' .pub')), c=document.getElementById(countId), e=document.getElementById(emptyId);
  return function(){var n=0;items.forEach(function(el){var s=test(el);el.hidden=!s;if(s)n++;});
    c.textContent=n+(n===1?' work':' works');e.hidden=!!n;};
}
var q2=document.getElementById('q2'), mf=document.getElementById('mf');
var a2=wire('l2','c2','e2',function(el){var t=q2.value.trim().toLowerCase();
  return (!mf.value||(' '+el.dataset.m+' ').indexOf(' '+mf.value+' ')>-1)&&(!t||el.textContent.toLowerCase().indexOf(t)>-1);});
q2.addEventListener('input',a2); mf.addEventListener('change',a2);

var q=document.getElementById('q'), filter='all', btns=[].slice.call(document.querySelectorAll('.filters button'));
var a1=wire('list','count','empty',function(el){var t=q.value.trim().toLowerCase();
  return (filter==='all'||el.dataset.t===filter)&&(!t||el.textContent.toLowerCase().indexOf(t)>-1);});
btns.forEach(function(b){b.addEventListener('click',function(){filter=b.dataset.f;
  btns.forEach(function(o){o.setAttribute('aria-pressed',o===b);});a1();});});
q.addEventListener('input',a1);

var qs=new URLSearchParams(location.search).get('q');
if(qs){qs=qs.replace(/\+/g,' ');q.value=qs;q2.value=qs;}
a1();a2();
"""
write('publications/index.html', page(
    'publications/', 'Publications · Spatial Intelligence Collective',
    f'{fmt(T["publications"])} publications by members of the Spatial Intelligence Collective, {T["multi_fellow"]} of them written by two or more fellows, with each member\'s own research record.',
    pubs_body, 'publications', script=pubs_js))


# ================================================================== learn/
LAB = 'https://lab.spatialintelligence.network'
labs = [('india', 'India', '725 districts', 81), ('brazil', 'Brazil', '558 microregions', 46),
        ('venezuela', 'Venezuela', '335 municipalities', 24)]
lab_li = ''.join(
    f'<li><a class="row" href="{LAB}/{k}"><span class="k">{n}</span>'
    f'<span class="v">{u}, {v} variables. Open the map, the Calculator and the Composer.</span></a></li>'
    for k, n, u, v in labs)
lessons = [('spatial-autocorrelation', "Spatial autocorrelation and Moran's I",
            "What it means for nearby places to resemble each other, how spatial weights are built, and how to compute and test global Moran's I."),
           ('hot-spot-analysis', 'LISA and hot-spot analysis',
            'Local indicators of spatial association and Getis-Ord Gi*, for finding where clusters and outliers sit on the map.'),
           ('interpolation', 'Interpolation, variograms and kriging',
            'Estimating values between observations, from inverse distance weighting to the variogram and ordinary kriging.')]
les_li = ''.join(
    f'<li><a class="row" href="{LAB}/spatstat/{k}/"><span class="k">{esc(t)}</span><span class="v">{esc(d)}</span></a></li>'
    for k, t, d in lessons)
learn_body = f"""<section class="page-head">
  <div class="wrap">
    <h1>Learn</h1>
    <p class="lede">Open tools for students and researchers who want to learn spatial methods by using them. Everything here runs in the browser, needs no installation or account, and is free for teaching and research.</p>
    <div class="cta">
      <a class="btn solid" href="{LAB}/india">Open the SIC Lab</a>
      <a class="btn" href="{LAB}/spatstat/">Start the tutorials</a>
    </div>
  </div>
</section>

<section id="lab">
  <div class="wrap">
    <p class="label">The SIC Lab</p>
    <h2>A map, a toolbox, and open data.</h2>
    <p class="lede muted">Choose a variable and the Lab maps it across every district or municipality. The Calculator lets you wire variables into a composite index or drop in a method: spatial weights, global Moran's I, LISA clusters, Getis-Ord Gi* hot spots, the Gini and Theil inequality indices, and OLS and geographically weighted regression. Every result can go back onto the map, into the Composer as a finished map, or out as CSV, GeoJSON, or a shapefile.</p>
    <ul class="rows">{lab_li}</ul>
  </div>
</section>

<section id="tutorials">
  <div class="wrap">
    <p class="label">Tutorials</p>
    <h2>Spatial statistics, step by step.</h2>
    <p class="lede muted">Each lesson explains a method visually and then lets you run it in Python inside the page, first on teaching data and then on real census data from the Lab.</p>
    <ul class="rows">{les_li}</ul>
    <p class="more"><a href="{LAB}/spatstat/">All lessons</a></p>
  </div>
</section>

<section id="open-data">
  <div class="wrap">
    <p class="label">Open data</p>
    <h2>Use the data in your own work.</h2>
    <p class="lede muted">Every variable in the Lab is a plain JSON file that can be read from a notebook, a script, or a web page, for example <code>{LAB}/v1/india/literacy_rate.json</code>. The catalogue for each country is at <a href="{LAB}/v1/india/meta.json">/v1/india/meta.json</a>, <a href="{LAB}/v1/brazil/meta.json">/v1/brazil/meta.json</a>, and <a href="{LAB}/v1/venezuela/meta.json">/v1/venezuela/meta.json</a>. Sources and licences are listed with each file and in the Lab's Sources panel.</p>
  </div>
</section>"""
learn_ld = {'@context': 'https://schema.org', '@type': 'Course', 'name': 'Spatial statistics with the SIC Lab',
            'description': 'Interactive lessons on spatial autocorrelation, hot-spot analysis and interpolation, with Python that runs in the browser.',
            'url': f'{SITE}/learn/', 'isAccessibleForFree': True,
            'provider': {'@type': 'Organization', 'name': 'Spatial Intelligence Collective', 'url': f'{SITE}/'}}
write('learn/index.html', page(
    'learn/', 'Learn · Spatial Intelligence Collective',
    'The SIC Lab and tutorials: open data and spatial statistics that run in the browser, free for students and researchers.',
    learn_body, 'learn', jsonld=learn_ld))

# ================================================================== index.html regions
idx_path = os.path.join(ROOT, 'index.html')
idx = open(idx_path).read()


def region(name, content):
    global idx
    pat = re.compile(r'(<!--b:%s-->).*?(<!--/b:%s-->)' % (name, name), re.S)
    if not pat.search(idx):
        sys.exit(f'index.html is missing the <!--b:{name}--> region')
    idx = pat.sub(lambda m: m.group(1) + content + m.group(2), idx)


region('facts', f'<li><b>{N_FELLOWS}</b> fellows</li><li><b>{N_UNIS}</b> universities</li><li><b>{N_COUNTRIES}</b> countries</li>')

recent = [w for w in OA['multi_fellow'] if w['type'] in ('article', 'review', 'book')][:4]
work_li = ''.join(
    f'<li><span class="y">{w["year"]}</span><span><a class="k" href="{esc(w["doi"] or "publications/#together")}" target="_blank" rel="noopener">{esc(w["title"])}</a>'
    f'<span class="meta">{esc(w["venue"])} · {", ".join(esc(BY_ID[i]["name"]) for i in w["members"])}</span></span></li>'
    for w in recent)
region('work', f"""
    <ul class="rows dated">{work_li}</ul>
    <p class="more"><a href="publications/#together">All {T['multi_fellow']} works by two or more fellows</a> · <a href="publications/">{fmt(T['publications'])} publications by members</a></p>
    """)

by_count = Counter(p['country'] for p in academics)
cs = [('the ' + c if c.startswith('United') else c) for c, _ in sorted(by_count.items(), key=lambda x: (-x[1], x[0]))]
COUNTRY_LIST = ', '.join(cs[:-1]) + ', and ' + cs[-1]
small = lambda p: f'<li><a class="n" href="people/#{p["id"]}">{esc(p["name"])}</a><span class="a">{esc(p["institution"])}</span></li>'
region('people', f"""
    <ul class="facts reach"><li><b>{N_FELLOWS}</b> fellows</li><li><b>{N_UNIS}</b> universities</li><li><b>{N_COUNTRIES}</b> countries</li><li><b>{N_DISC}</b> disciplines</li></ul>
    <p class="lede reach-lede">Members range from assistant to emeritus professors in geography, planning, geomatics engineering, remote sensing, information management, computing science, business, economics, and nursing, at universities in {COUNTRY_LIST}. That breadth lets the Collective build and fund research across disciplines and across borders.</p>
    <div class="group">
      <h3>Lead</h3>
      <ul class="people">{''.join(f'<li><a class="n" href="people/#{p["id"]}">{esc(p["name"])}</a><span class="a">{affil(p)}</span></li>' for p in lead)}</ul>
    </div>
    <details class="group fold" data-fold>
      <summary><h3>Fellows <span class="c">{N_FELLOWS}</span></h3></summary>
      <ul class="people cols">{''.join(small(p) for p in fellows)}</ul>
    </details>
    <details class="group fold" data-fold>
      <summary><h3>Doctoral researchers <span class="c">{len(doctoral)}</span></h3></summary>
      <ul class="people cols">{''.join(small(p) for p in doctoral)}</ul>
    </details>
    <p class="more"><a href="people/">Full directory, with each member's research profiles</a></p>
    """)

org_ld = {'@context': 'https://schema.org', '@type': 'Organization', 'name': 'Spatial Intelligence Collective',
          'url': f'{SITE}/', 'logo': f'{SITE}/assets/art/logo-sic.png',
          'description': 'A research network studying cities and regions as complex adaptive systems.',
          'founder': {'@type': 'Person', 'name': lead[0]['name'],
                      'affiliation': {'@type': 'CollegeOrUniversity', 'name': lead[0]['institution']}},
          'member': [person_ld(p) for p in fellows]}
region('jsonld', f'<script type="application/ld+json">{json.dumps(org_ld, ensure_ascii=False)}</script>')
open(idx_path, 'w').write(idx)

# ================================================================== sitemap, robots
today = datetime.date.today().isoformat()
urls = ['', 'people/', 'publications/', 'learn/', 'strange/']
write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
      + ''.join(f'  <url><loc>{SITE}/{u}</loc><lastmod>{today}</lastmod></url>\n' for u in urls) + '</urlset>\n')
write('robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n')

print(f'built: {N_FELLOWS} fellows, {N_UNIS} universities, {N_COUNTRIES} countries; '
      f'{fmt(T["publications"])} publications, {T["multi_fellow"]} multi-fellow; masthead {N_MAST}')
