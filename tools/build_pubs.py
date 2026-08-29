#!/usr/bin/env python3
"""Generate publications/index.html from the real publication record."""
import json, os, html, re

HERE = os.path.dirname(__file__)
pubs = json.load(open(os.path.join(HERE, 'pubs.json')))

# Recent work verified on Google Scholar / Springer, not yet in the site JSON-LD.
EXTRA = [
 {"title":"Regional and Urban Change and Geographical Information Systems and Science: An Analysis of Northern Canada","year":"2026","venue":"Springer","authors":["Vaz, E."],"kind":"Book"},
 {"title":"Adaptive multi-criteria ecotopes: a memory-embedded cellular automata framework","year":"2026","venue":"Open Geosciences","authors":["Vaz, E."],"kind":"Article"},
 {"title":"GIScience as a Tool for Environmental Response in Northern Canada","year":"2026","venue":"Regional and Urban Change and GIScience (Springer)","authors":["Vaz, E."],"kind":"Chapter"},
 {"title":"Inuit Communities in the North","year":"2026","venue":"Regional and Urban Change and GIScience (Springer)","authors":["Vaz, E."],"kind":"Chapter"},
 {"title":"Food Scarcity in Nunavut: Socio-Economic, Cultural, and Environmental Dimensions","year":"2026","venue":"Regional and Urban Change and GIScience (Springer)","authors":["Vaz, E."],"kind":"Chapter"},
 {"title":"Geographic Information System (GIS) methodology","year":"2025","venue":"Thematic Encyclopedia of Regional Science","authors":["Vaz, E."],"kind":"Chapter"},
 {"title":"Self-organising maps for exploring the change in Portuguese communities in Toronto","year":"2025","venue":"Handbook on Big Data, Artificial Intelligence and Cities","authors":["Vaz, E."],"kind":"Chapter"},
 {"title":"Quantum Computational Paradigms in Spatial Analytics: Advancing Environmental and Resource Econometrics","year":"2024","venue":"Regional Knowledge Economies (Springer)","authors":["Vaz, E."],"kind":"Chapter"},
]

BOOKS = [
 ("978-3-032-19210-3","Regional and Urban Change and Geographical Information Systems and Science","An Analysis of Northern Canada","2026"),
 ("978-3-031-76906-1","Regional Knowledge Economies","Technology, Geography, and Innovation in the Digital Era","2024"),
 ("978-3-031-24731-6","Regional and Urban Change and Geographical Information Systems and Science","An Analysis of Ontario, Canada","2023"),
 ("978-3-031-19871-7","Geography of Happiness","A Spatial Analysis of Subjective Well-Being","2023"),
 ("978-3-662-62177-6","Sustainable Development in Southern Europe","Spatial Analysis of Regional Challenges","2020"),
 ("978-3-030-36479-3","Regional Intelligence","Spatial Analysis and Anthropogenic Regional Challenges in the Digital Age","2020"),
 ("978-3-319-95135-5","Resilience and Regional Dynamics","An International Approach to a New Research Agenda","2018"),
]

# ------------------------------------------------------------------ themes
THEMES = [
 ("quantum",   "Quantum",       r"quantum"),
 ("complexity","Complexity",    r"nash|equilibri|network|cluster structur|resilien|emergen|graph theory|complex|innovation support|gravit|multi-criteria|biplot"),
 ("geoai",     "GeoAI & ML",    r"machine learning|artificial intelligence|neural|deep learn|random forest|big data|self-organi|crowdsourc|volunteered|citizen sci|collaborative mapping"),
 ("geocomp",   "Geocomputation",r"cellular automata|agent-based|simulat|markov|predicting urban growth|forecast|scenario|model"),
 ("spatial",   "Spatial Analysis", r"spatial|geovisual|landscape metric|hedonic|dasymetric|autocorrelation|mapping|geographic information|gis|remote sens|earth observation|land cover|land use|geoinformation|coastal|vulnerab"),
 ("regional",  "Regional & Urban", r"."),
]
def theme(p):
    t = f"{p['title']} {p.get('venue') or ''}".lower()
    for key, _, pat in THEMES:
        if re.search(pat, t): return key
    return "regional"

for p in pubs:
    p.setdefault('kind', 'Article')
rows = pubs + EXTRA
for p in rows:
    p['theme'] = theme(p)
rows.sort(key=lambda p: (-int(p['year']), p['title']))

def esc(s): return html.escape(s or '')

items = []
for p in rows:
    au = "; ".join(p['authors']) if p['authors'] else ""
    ven = esc(p.get('venue') or '')
    meta = f"<span class='v'>{ven}</span>" if ven else ""
    sep = " · " if au and ven else ""
    items.append(
      f'<article class="pub" data-t="{p["theme"]}" data-k="{esc(p["kind"]).lower()}">'
      f'<div class="y">{p["year"]}</div><div>'
      f'<div class="t">{esc(p["title"])}</div>'
      f'<div class="a">{esc(au)}{sep}{meta}</div>'
      f'</div></article>')

chips = ''.join(
  f'<button data-f="{k}" aria-pressed="false">{esc(lbl)}</button>'
  for k, lbl, _ in THEMES)

DOI_ISBN = {"978-3-032-19210-3": "978-3-032-19211-0"}   # print ISBN -> eBook ISBN used in the DOI
books = ''.join(
  f'<a class="book" href="https://link.springer.com/book/10.1007/{DOI_ISBN.get(isbn, isbn)}" target="_blank" rel="noopener">'
  f'<img src="../assets/covers/{isbn}.webp" alt="{esc(t)} — {esc(sub)}" loading="lazy">'
  f'<h3>{esc(t)}</h3><span>{esc(sub)}</span><span>{yr} · Springer</span></a>'
  for isbn, t, sub, yr in BOOKS)

PAGE = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Publications — Eric Vaz Lab</title>
<meta name="description" content="Peer-reviewed articles, book chapters and Springer monographs by Eric Vaz on geocomputation, GeoAI, complexity science and quantum spatial analysis.">
<link rel="preload" href="../assets/fonts/vazhand.woff2?v=3" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="../assets/css/lab.css?v=3">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><circle cx='16' cy='16' r='4' fill='%23111'/><circle cx='6' cy='7' r='2' fill='%23111'/><circle cx='26' cy='9' r='2' fill='%23111'/><circle cx='8' cy='26' r='2' fill='%23111'/><circle cx='25' cy='25' r='2' fill='%23111'/><g stroke='%23111' stroke-width='1' fill='none'><path d='M16 16 6 7M16 16l10-7M16 16 8 26M16 16l9 9'/></g></svg>">
</head>
<body>

<header class="hdr">
  <div class="wrap">
    <a class="brand" href="../" aria-label="Eric Vaz Lab"><img src="../assets/art/logo-ericvazlab.png" alt="Eric Vaz Lab" width="345" height="72"></a>
    <button class="burger" aria-label="Menu" aria-expanded="false"><span></span><span></span><span></span></button>
    <nav class="nav">
      <a href="../#research">Research</a>
      <a href="./">Publications</a>
      <a href="../#people">People</a>
      <a href="../#lab">The Lab</a>
      <a href="../#news">News</a>
      <a href="../#contact">Contact</a>
    </nav>
  </div>
</header>

<section class="page-hero">
  <div class="wrap">
    <h1>Publications</h1>
    <p class="lede">Peer-reviewed articles, chapters and monographs spanning geocomputation,
      spatial analysis, GeoAI, complexity science and — most recently — quantum approaches to
      spatial problems. Filter by research area or search the full record.</p>
    <div class="metrics">
      <div><b>90+</b><span>peer-reviewed publications</span></div>
      <div><b>3,843</b><span>citations</span></div>
      <div><b>32</b><span>h-index</span></div>
      <div><b>7</b><span>Springer volumes</span></div>
    </div>
  </div>
</section>

<section class="sec" id="articles">
  <div class="wrap">
    <div class="sec-head"><p class="label">Curated Record · {len(rows)} entries</p></div>
    <div class="filters">
      <button data-f="all" aria-pressed="true">All</button>
      {chips}
    </div>
    <input class="search" id="q" type="search" placeholder="Search titles, authors, journals…" aria-label="Search publications">
    <p class="count" id="count"></p>
    <div id="list">
      {''.join(items)}
    </div>
    <p class="count" id="empty" style="display:none">No publications match that filter.</p>
  </div>
</section>

<section class="sec alt" id="books">
  <div class="wrap">
    <div class="sec-head"><p class="label">Books &amp; Edited Volumes</p></div>
    <div class="books">{books}</div>
  </div>
</section>

<footer class="ftr">
  <div class="wrap">
    <div class="ftr-btm" style="margin-top:0;border-top:0">
      <span>© <span id="yr">2026</span> Eric Vaz Lab.</span>
      <span><a href="https://scholar.google.com/citations?user=EfpbSEYAAAAJ" target="_blank" rel="noopener">Google Scholar</a> ·
            <a href="https://orcid.org/0000-0003-1738-2677" target="_blank" rel="noopener">ORCID</a> ·
            <a href="../">Back to the lab</a></span>
    </div>
  </div>
</footer>

<script>
document.getElementById('yr').textContent = new Date().getFullYear();
var b=document.querySelector('.burger'), n=document.querySelector('.nav');
b.addEventListener('click',function(){{var o=n.classList.toggle('open');b.setAttribute('aria-expanded',o);}});

var items=[].slice.call(document.querySelectorAll('.pub')),
    btns=[].slice.call(document.querySelectorAll('.filters button')),
    q=document.getElementById('q'), count=document.getElementById('count'),
    empty=document.getElementById('empty'), filter='all';

function apply(){{
  var term=q.value.trim().toLowerCase(), n=0;
  items.forEach(function(el){{
    var okF = filter==='all' || el.dataset.t===filter;
    var okQ = !term || el.textContent.toLowerCase().indexOf(term)>-1;
    var show = okF && okQ;
    el.style.display = show ? '' : 'none';
    if(show) n++;
  }});
  count.textContent = n + (n===1?' publication':' publications');
  empty.style.display = n ? 'none' : '';
}}
btns.forEach(function(btn){{
  btn.addEventListener('click',function(){{
    filter=btn.dataset.f;
    btns.forEach(function(o){{o.setAttribute('aria-pressed', o===btn);}});
    apply();
  }});
}});
q.addEventListener('input',apply);

// deep link: publications/?q=quantum
var qs=new URLSearchParams(location.search).get('q');
if(qs){{ q.value=qs.replace(/\\+/g,' '); }}
apply();
</script>
</body>
</html>
"""

out = os.path.join(HERE, '..', 'publications')
os.makedirs(out, exist_ok=True)
open(os.path.join(out, 'index.html'), 'w').write(PAGE)

from collections import Counter
c = Counter(p['theme'] for p in rows)
print(f"publications/index.html — {len(rows)} entries")
for k, l, _ in THEMES: print(f"  {l:16s} {c.get(k,0)}")

