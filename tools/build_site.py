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
CSS_V = 17


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
    if p['category'] not in ('lead', 'fellow', 'honorary', 'advisory', 'doctoral', 'editor'):
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
academics = [p for p in lead + fellows if not p.get('nonacademic')]   # university-based members
practitioners = [p for p in fellows if p.get('nonacademic') and p['category'] != 'honorary']
N_FELLOWS = len(fellows)
N_UNIS = len({p['institution'] for p in academics})
N_COUNTRIES = len({p['country'] for p in academics})
N_DISC = META['disciplines']
board = az([p for p in PEOPLE if p.get('strange') == 'board'])
director_p = [p for p in PEOPLE if p.get('strange') == 'director']
manager_p = [p for p in PEOPLE if p.get('strange') == 'manager']
fiction_p = [p for p in PEOPLE if p.get('strange') == 'fiction']   # masthead-only editors (category 'editor', not fellows)
N_MAST = len(director_p) + len(manager_p) + len(fiction_p) + len(board)
T = OA['totals']
indexed = len(OA['members_indexed'])
UPDATED = datetime.date.fromisoformat(OA['updated'])
UPDATED_TXT = f'{UPDATED.day} {UPDATED:%B %Y}'
fmt = lambda n: f'{n:,}'


def nav(depth, here=''):
    up = '../' * depth
    items = [('Research', f'{up}#research', ''), ('People', f'{up}people/', 'people'),
             ('STRANGE', f'{up}strange/', 'strange'), ('Publications', f'{up}publications/', 'publications'),
             ('Learn', f'{up}learn/', 'learn'), ('About', f'{up}about/', 'about'),
             ('Contact', f'{up}#contact', '')]
    return '\n      '.join(
        f'<a href="{h}"' + (' aria-current="page"' if k and k == here else '') + f'>{t}</a>'
        for t, h, k in items)


ICON = "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='124 109 649 649' fill='none' stroke='%23111' stroke-width='24.0' stroke-linecap='round' stroke-linejoin='round'><path d='M534.0 127.0 L558.0 127.9 L581.0 132.4 L603.0 140.6 L623.0 152.2 L640.0 166.6 L653.1 183.0 L662.4 201.0 L667.8 221.0 L668.8 242.0 L664.8 264.0 L657.0 283.9 L638.7 318.0 L634.3 334.0 L634.3 349.0 L640.1 394.0 L641.8 424.0 L640.7 456.0 L636.5 489.0 L630.9 515.0 L623.5 540.0 L614.4 564.0 L604.0 585.8 L585.0 616.3 L563.0 641.5 L540.0 659.3 L528.0 665.6 L516.0 669.9 L501.0 672.6 L486.0 672.1 L472.0 668.6 L458.4 662.0 L447.0 653.6 L435.7 642.0 L406.0 600.0 L400.0 595.8 L394.0 594.9 L386.0 597.5 L377.0 603.3 L321.0 650.8 L287.0 674.8 L271.0 683.2 L258.0 687.9 L247.0 689.5 L238.0 687.6 L232.5 683.0 L229.1 675.0 L228.4 665.0 L230.0 653.0 L240.1 622.0 L258.5 585.0 L280.6 549.0 L306.8 512.0 L333.0 478.8 L381.7 421.0 L399.2 398.0 L421.8 363.0 L435.0 337.0 L437.8 325.0 L436.9 314.0 L417.8 270.0 L414.1 257.0 L412.1 244.0 L411.9 230.0 L413.6 217.0 L417.3 204.0 L423.0 191.0 L431.2 178.0 L442.0 165.4 L454.0 154.9 L468.0 145.6 L483.0 138.2 L499.0 132.6 L516.0 128.8 L534.0 127.0'/><path d='M254.2 662.5 L489.8 377.5'/><path d='M436.0 379.3 L455.0 366.4 L471.0 357.7 L484.0 352.6 L497.0 350.5 L505.2 352.0 L512.2 358.0 L515.2 367.0 L515.0 381.1 L510.2 401.0 L503.0 420.0 L481.5 462.0 L449.6 511.0 L414.0 557.1'/><path d='M480.0 168.9 L489.0 168.0 L499.0 168.8 L508.0 171.1 L517.0 175.2 L525.0 180.9 L532.0 188.0 L537.3 196.0 L541.0 204.3 L545.8 194.0 L552.7 185.0 L561.0 177.8 L571.0 172.3 L582.0 168.9 L593.0 168.0 L604.0 169.4 L615.0 173.1 L624.0 178.5 L632.0 185.7 L638.2 194.0 L642.9 204.0 L645.4 214.0 L645.9 225.0 L644.4 235.0 L640.9 245.0 L634.0 256.0 L624.0 265.5 L613.0 271.7 L600.0 275.4 L590.0 276.0 L581.0 274.9 L564.0 268.2 L550.0 256.0 L544.7 248.0 L541.0 239.7 L536.2 250.0 L529.3 259.0 L521.0 266.2 L511.0 271.7 L500.0 275.1 L489.0 276.0 L478.0 274.6 L467.0 270.9 L453.0 261.3 L442.7 248.0 L436.9 232.0 L436.5 215.0 L441.1 199.0 L450.7 185.0 L464.0 174.7 L480.0 168.9'/><path d='M485.0 206.0 L492.0 205.3 L498.0 207.2 L503.0 211.4 L506.0 217.0 L506.7 224.0 L504.8 230.0 L500.6 235.0 L495.0 238.0 L488.0 238.7 L482.0 236.8 L477.0 232.6 L474.0 227.0 L473.3 220.0 L475.2 214.0 L479.4 209.0 L485.0 206.0'/><path d='M587.0 206.0 L594.0 205.3 L600.0 207.2 L605.0 211.4 L608.0 217.0 L608.7 224.0 L606.8 230.0 L602.6 235.0 L597.0 238.0 L590.0 238.7 L584.0 236.8 L579.0 232.6 L576.0 227.0 L575.3 220.0 L577.2 214.0 L581.4 209.0 L587.0 206.0'/><path d='M541.0 242.0 L554.0 268.0 L541.0 294.0 L528.0 268.0 L541.0 242.0'/><path d='M500.0 664.0 L500.0 740.0'/><path d='M556.0 664.0 L556.0 740.0'/></svg>"
OWL = '<svg class="brand-owl" viewBox="135 120 627 627" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M534.0 127.0 L558.0 127.9 L581.0 132.4 L603.0 140.6 L623.0 152.2 L640.0 166.6 L653.1 183.0 L662.4 201.0 L667.8 221.0 L668.8 242.0 L664.8 264.0 L657.0 283.9 L638.7 318.0 L634.3 334.0 L634.3 349.0 L640.1 394.0 L641.8 424.0 L640.7 456.0 L636.5 489.0 L630.9 515.0 L623.5 540.0 L614.4 564.0 L604.0 585.8 L585.0 616.3 L563.0 641.5 L540.0 659.3 L528.0 665.6 L516.0 669.9 L501.0 672.6 L486.0 672.1 L472.0 668.6 L458.4 662.0 L447.0 653.6 L435.7 642.0 L406.0 600.0 L400.0 595.8 L394.0 594.9 L386.0 597.5 L377.0 603.3 L321.0 650.8 L287.0 674.8 L271.0 683.2 L258.0 687.9 L247.0 689.5 L238.0 687.6 L232.5 683.0 L229.1 675.0 L228.4 665.0 L230.0 653.0 L240.1 622.0 L258.5 585.0 L280.6 549.0 L306.8 512.0 L333.0 478.8 L381.7 421.0 L399.2 398.0 L421.8 363.0 L435.0 337.0 L437.8 325.0 L436.9 314.0 L417.8 270.0 L414.1 257.0 L412.1 244.0 L411.9 230.0 L413.6 217.0 L417.3 204.0 L423.0 191.0 L431.2 178.0 L442.0 165.4 L454.0 154.9 L468.0 145.6 L483.0 138.2 L499.0 132.6 L516.0 128.8 L534.0 127.0"/><path d="M247.3 645.7 L472.0 373.9"/><path d="M272.0 666.1 L496.7 394.3"/><path d="M436.0 379.3 L455.0 366.4 L471.0 357.7 L484.0 352.6 L497.0 350.5 L505.2 352.0 L512.2 358.0 L515.2 367.0 L515.0 381.1 L510.2 401.0 L503.0 420.0 L481.5 462.0 L449.6 511.0 L414.0 557.1"/><path d="M486.0 166.9 L503.0 168.4 L519.0 175.0 L532.0 186.2 L541.0 200.9 L546.3 191.0 L554.0 182.0 L563.0 175.0 L573.0 170.2 L584.0 167.4 L596.0 166.9 L607.0 168.9 L617.4 173.0 L626.6 179.0 L634.0 186.2 L640.1 195.0 L644.5 205.0 L646.9 216.0 L647.0 227.0 L645.0 237.4 L641.0 247.4 L633.8 258.0 L624.0 267.0 L612.0 273.4 L599.0 276.8 L581.0 276.1 L564.0 269.6 L550.2 258.0 L541.0 243.1 L535.7 253.0 L528.0 262.0 L519.0 269.0 L509.0 273.8 L498.0 276.6 L486.0 277.1 L475.0 275.1 L464.6 271.0 L450.0 260.0 L440.3 246.0 L435.2 229.0 L435.9 211.0 L442.4 194.0 L454.0 180.2 L469.0 171.0 L486.0 166.9"/><path d="M482.0 190.0 L495.0 189.4 L507.0 193.7 L516.2 202.0 L522.0 214.0 L522.6 227.0 L518.3 239.0 L510.0 248.2 L498.0 254.0 L485.0 254.6 L473.0 250.3 L463.8 242.0 L458.0 230.0 L457.4 217.0 L461.7 205.0 L470.0 195.8 L482.0 190.0"/><path d="M584.0 190.0 L597.0 189.4 L609.0 193.7 L618.2 202.0 L624.0 214.0 L624.6 227.0 L620.3 239.0 L612.0 248.2 L600.0 254.0 L587.0 254.6 L575.0 250.3 L565.8 242.0 L560.0 230.0 L559.4 217.0 L563.7 205.0 L572.0 195.8 L584.0 190.0"/><path d="M486.0 210.7 L491.0 210.0 L495.0 211.1 L498.9 214.0 L501.3 218.0 L502.0 223.0 L500.9 227.0 L498.0 230.9 L494.0 233.3 L489.0 234.0 L485.0 232.9 L481.1 230.0 L478.7 226.0 L478.0 221.0 L479.1 217.0 L482.0 213.1 L486.0 210.7"/><path d="M588.0 210.7 L593.0 210.0 L597.0 211.1 L600.9 214.0 L603.3 218.0 L604.0 223.0 L602.9 227.0 L600.0 230.9 L596.0 233.3 L591.0 234.0 L587.0 232.9 L583.1 230.0 L580.7 226.0 L580.0 221.0 L581.1 217.0 L584.0 213.1 L588.0 210.7"/><path d="M541.0 242.0 L554.0 268.0 L541.0 294.0 L528.0 268.0 L541.0 242.0"/><path d="M500.0 664.0 L500.0 740.0"/><path d="M556.0 664.0 L556.0 740.0"/></svg>'


def page(path, title, desc, body, here, script='', jsonld=None, og_image='assets/art/og-sic-owl.png'):
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
    <a class="brand" href="{up or './'}">{OWL}<span>Spatial Intelligence Collective</span></a>
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
    <div class="ftr-id"><a class="ftr-brand" href="{up or './'}">{OWL}<span>Spatial Intelligence Collective</span></a><span>© <span id="yr">2026</span> Spatial Intelligence Collective</span></div>
    <span><a href="{up}people/">People</a> · <a href="{up}publications/">Publications</a> · <a href="{up}learn/">Learn</a> · <a href="{up}strange/">STRANGE</a> · <a href="{up}about/">How the Collective works</a> · <a href="{up}#flows">Everything flows</a></span>
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
    if p['category'] == 'doctoral':
        return f'{esc(p["position"])}, {esc(p["institution"])}'
    return f'{esc(p["position"])} · {esc(p["institution"])}'


PILL = {'lead': 'Director', 'honorary': 'Honorary fellow', 'advisory': 'Advisory board'}


def pills(p):
    out = [PILL[p['category']]] if p['category'] in PILL else []
    if p.get('strange') == 'board':
        out.append('STRANGE board')
    return ''.join(f' <span class="tag">{t}</span>' for t in out)


def person_ld(p):
    same = []
    if p.get('orcid'):
        same.append(f'https://orcid.org/{p["orcid"]}')
    if p.get('scholar'):
        same.append(f'https://scholar.google.com/citations?user={p["scholar"]}')
    d = {'@type': 'Person', 'name': p['name'], 'jobTitle': p['position'],
         'affiliation': {'@type': 'Organization' if p.get('nonacademic') else 'CollegeOrUniversity', 'name': p['institution']},
         'url': f'{SITE}/people/#{p["id"]}'}
    if same:
        d['sameAs'] = same
    return d


# ================================================================== people/
def entry(p):
    extra = f'<p class="d">{esc(p["research"])}</p>' if p.get('research') else ''
    return (f'<li id="{p["id"]}"><span class="n">{esc(p["name"])}{pills(p)}</span>'
            f'<span class="a">{affil(p)}</span>{extra}{links(p)}</li>')


sys.path.insert(0, HERE)
from build_map import network_map
PLACES = load('places.json')['places']
LAND = load('world-land.geojson')
for p in lead + fellows + doctoral:
    if p['institution'] not in PLACES:
        sys.exit(f'{p["id"]}: add "{p["institution"]}" to content/places.json')
NETMAP = network_map(lead + fellows + doctoral, PLACES, LAND)
N_MEMBERS = len(lead) + len(fellows)


people_body = f"""<section class="page-head">
  <div class="wrap">
    <h1>People</h1>
    <p class="lede">The Spatial Intelligence Collective is a research network based at Toronto Metropolitan University. Its fellows hold appointments at their own universities and organizations and work across geography, planning, geomatics engineering, remote sensing, information management, computing science, business, economics, and nursing. Fellowship is by invitation.</p>
    <ul class="metrics"><li><b>{N_FELLOWS}</b> fellows</li><li><b>{N_UNIS}</b> universities</li><li><b>{N_COUNTRIES}</b> countries</li><li><b>{N_DISC}</b> disciplines</li></ul>
  </div>
</section>

<section id="fellows">
  <div class="wrap">
    <p class="label">Director and fellows · {N_MEMBERS}</p>
    <ul class="people cols">{''.join(entry(p) for p in az(lead + fellows))}</ul>
  </div>
</section>

<section id="doctoral">
  <div class="wrap">
    <p class="label">Doctoral researchers · {len(doctoral)}</p>
    <ul class="people cols">{''.join(entry(p) for p in doctoral)}</ul>
    <p class="more">Researchers whose work fits the Collective are welcome to <a href="mailto:evaz@torontomu.ca?subject=Spatial%20Intelligence%20Collective">write to Eric Vaz</a>. Each fellow's own research record is linked from their entry, and the <a href="../publications/">publications page</a> lists work fellows have written together.</p>
  </div>
</section>

<section id="map">
  <div class="wrap">
    <p class="label">Where we are</p>
    <figure class="netmap-fig">{NETMAP}
      <figcaption>{len(lead + fellows + doctoral)} members at {len({p['institution'] for p in lead + fellows + doctoral})} universities and organizations in {len({p['country'] for p in lead + fellows + doctoral})} countries, linked to Toronto, where the Collective is based.</figcaption>
    </figure>
  </div>
</section>"""

people_ld = {'@context': 'https://schema.org', '@type': 'ItemList', 'name': 'Members of the Spatial Intelligence Collective',
             'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'item': person_ld(p)}
                                 for i, p in enumerate(lead + fellows + doctoral)]}
write('people/index.html', page(
    'people/', 'People · Spatial Intelligence Collective',
    f'The director, {N_FELLOWS} fellows and doctoral researchers of the Spatial Intelligence Collective, at {N_UNIS} universities in {N_COUNTRIES} countries.',
    people_body, 'people', jsonld=people_ld))

# ================================================================== strange/
mast = ''.join(f'<li><span class="n">{esc(p["name"])}</span><span class="a">Director</span></li>' for p in director_p)
mast += ''.join(f'<li><span class="n">{esc(p["name"])}</span><span class="a">Editorial manager</span></li>' for p in manager_p)
mast += ''.join(f'<li><span class="n">{esc(p["name"])}</span><span class="a">Fiction editor</span></li>' for p in fiction_p)
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


pubs_body = f"""<section class="page-head">
  <div class="wrap">
    <h1>Publications</h1>
    <p class="lede">Work that fellows have written together, and a link to each member's own research record. Much of it predates the Collective and shows where members' research already meets.</p>
    <p class="prov">Source: OpenAlex, matched to each member by ORCID · updated {UPDATED_TXT}. Members can correct or withdraw their records by writing to Eric Vaz.</p>
  </div>
</section>

<section id="together">
  <div class="wrap">
    <p class="label">Written together</p>
    <h2>Work by two or more fellows.</h2>
    <div class="tools">
      <label class="pick-m"><span>Fellow</span>
        <select id="mf"><option value="">All fellows</option>{opts}</select></label>
      <input class="search" id="q2" type="search" placeholder="Search titles and journals" aria-label="Search works by two or more fellows">
    </div>
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
</section>"""

pubs_js = r"""
function wire(listId, emptyId, test){
  var items=[].slice.call(document.querySelectorAll('#'+listId+' .pub')), e=document.getElementById(emptyId);
  return function(){var n=0;items.forEach(function(el){var s=test(el);el.hidden=!s;if(s)n++;});
    e.hidden=!!n;};
}
var q2=document.getElementById('q2'), mf=document.getElementById('mf');
var a2=wire('l2','e2',function(el){var t=q2.value.trim().toLowerCase();
  return (!mf.value||(' '+el.dataset.m+' ').indexOf(' '+mf.value+' ')>-1)&&(!t||el.textContent.toLowerCase().indexOf(t)>-1);});
q2.addEventListener('input',a2); mf.addEventListener('change',a2);


var qs=new URLSearchParams(location.search).get('q');
if(qs){qs=qs.replace(/\+/g,' ');q2.value=qs;}
a2();
"""
write('publications/index.html', page(
    'publications/', 'Publications · Spatial Intelligence Collective',
    'Work written together by fellows of the Spatial Intelligence Collective, with links to each member\'s own research record.',
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

# ================================================================== about/
FAQ = [
    ('What is the Spatial Intelligence Collective?',
     'The Spatial Intelligence Collective (SIC) is an international network of researchers and practitioners who study cities and regions as complex adaptive systems through geocomputation, GeoAI, spatial statistics, and spatial econometrics. It grew out of the Laboratory for Geocomputation at Toronto Metropolitan University. SIC is preparing the first issue of STRANGE, a magazine of space, place, and imagination, and maintains the SIC Lab, an open resource for spatial data and methods.'),
    ('Is SIC a university research centre?',
     'SIC is a faculty-led research network and has no formal research centre status at Toronto Metropolitan University or any other institution. It is unincorporated, has no employees, holds no funds, and signs no contracts of its own; any funding for its activities is held by an eligible host institution under that institution\'s rules. Members take part in their individual capacities, and membership does not imply that their institutions endorse SIC.'),
    ('Who leads the Collective?',
     'SIC is led by its founder and Director, Eric Vaz, who sets its direction, invites members, and appoints its editors and organizers. The Director represents the Collective without speaking on behalf of individual members, and may seek the advice of Fellows on any matter.'),
    ('How do people join?',
     'Membership is by invitation of the Director and begins when the invitation is accepted. Fellows are researchers and practitioners whose work advances the purpose of the Collective, and Honorary Fellows are distinguished contributors to the field. Doctoral Members are doctoral researchers whose work falls within its remit.'),
    ('What does membership ask of me?',
     'Membership carries no obligation to contribute time, money, or work. Events, joint projects, and STRANGE are entirely voluntary. Members may leave at any time.'),
    ('How do members work together?',
     'Members treat one another with respect and fairness. Seniority is never used to press junior colleagues into taking on work, sharing data, or accepting authorship. Unpublished work and data shared through SIC are kept in confidence, subject to the permission of those entitled to share them and to any legal requirement.'),
    ('Does membership help me publish in journals edited by members?',
     'No. Membership gives no preferential treatment in any academic journal edited by a member.'),
    ('Who owns the work members produce?',
     'Its authors and their institutions. SIC claims no rights over its members\' work, and membership creates no entitlement to authorship, funding, data, or intellectual property.'),
    ('How is my information used?',
     'With each member\'s agreement, SIC publishes a profile drawing on public sources such as ORCID and OpenAlex. Members may ask for their profile to be corrected or removed at any time.'),
    ('Who can I contact with a concern?',
     'Concerns can be raised with the Director. Members remain free to use their own institutions\' reporting channels.'),
    ('Why an owl?',
     'Our emblem comes from the silver tetradrachm of ancient Athens, where the little owl, Athene noctua, stood beside Athena. As Athena Polias she guarded the city, and Rome honoured her as Minerva, goddess of wisdom and craft. The owl suits a collective that studies cities: it perceives depth in low light, and some owls find their prey by sound alone.\n\nHegel wrote that the owl of Minerva spreads its wings only with the falling of dusk, when an age can be understood because it has already passed. We read that line as a challenge for the spatial sciences, which can study cities and regions while they are still changing.\n\nOur owl is drawn only with isolines, the lines of equal value that cartographers use to read terrain. An ancient figure of wisdom is set down in the working language of spatial analysis.'),
]
faq_dl = ''.join(f'<div class="qa{" qa-owl" if q == "Why an owl?" else ""}"><h2>{esc(q)}</h2>' + (f'<img class="owl-emblem" src="../assets/art/owl.svg" alt="" width="72" height="72">' if q == "Why an owl?" else '') + ''.join(f'<p>{esc(x)}</p>' for x in a.split('\n\n')) + '</div>' for q, a in FAQ)
about_body = f"""<section class="page-head">
  <div class="wrap">
    <h1>How the Collective works</h1>
    <p class="lede">A short guide for colleagues who are members, have been invited, or are curious about the Collective.</p>
  </div>
</section>

<section id="faq">
  <div class="wrap faq">{faq_dl}
    <p class="more">Anything else? <a href="mailto:evaz@torontomu.ca?subject=Spatial%20Intelligence%20Collective">Write to the Director</a>.</p>
  </div>
</section>"""
about_ld = {'@context': 'https://schema.org', '@type': 'FAQPage', 'url': f'{SITE}/about/',
            'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in FAQ]}
write('about/index.html', page(
    'about/', 'How the Collective works · Spatial Intelligence Collective',
    'What the Spatial Intelligence Collective is, who leads it, how members join, and what membership does and does not ask.',
    about_body, 'about', jsonld=about_ld))

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
    <p class="more"><a href="publications/#together">All work by two or more fellows</a> · <a href="publications/#records">Members' research records</a></p>
    """)

by_count = Counter(p['country'] for p in academics)
cs = [('the ' + c if c.startswith('United') or c == 'Netherlands' else c) for c, _ in sorted(by_count.items(), key=lambda x: (-x[1], x[0]))]
COUNTRY_LIST = ', '.join(cs[:-1]) + ', and ' + cs[-1]
PRACT = ', with practitioners in ' + ' and '.join(sorted({p['country'] for p in practitioners})) if practitioners else ''
small = lambda p: f'<li><a class="n" href="people/#{p["id"]}">{esc(p["name"])}</a>{pills(p)}<span class="a">{esc(p["institution"])}</span></li>'
region('people', f"""
    <ul class="facts reach"><li><b>{N_FELLOWS}</b> fellows</li><li><b>{N_UNIS}</b> universities</li><li><b>{N_COUNTRIES}</b> countries</li><li><b>{N_DISC}</b> disciplines</li></ul>
    <p class="lede reach-lede">Members range from assistant to emeritus professors in geography, planning, geomatics engineering, remote sensing, information management, computing science, business, economics, and nursing, at universities in {COUNTRY_LIST}{PRACT}. Together, members can develop joint research and pursue funding across disciplines and national borders.</p>
    <details class="group fold" data-fold>
      <summary><h3>Director and fellows <span class="c">{N_MEMBERS}</span></h3></summary>
      <ul class="people cols">{''.join(small(p) for p in az(lead + fellows))}</ul>
    </details>
    <details class="group fold" data-fold>
      <summary><h3>Doctoral researchers <span class="c">{len(doctoral)}</span></h3></summary>
      <ul class="people cols">{''.join(small(p) for p in doctoral)}</ul>
    </details>
    <figure class="netmap-fig">{NETMAP}</figure>
    <p class="more"><a href="people/">Full directory, with each member's research profiles</a></p>
    """)

org_ld = {'@context': 'https://schema.org', '@type': 'Organization', 'name': 'Spatial Intelligence Collective',
          'url': f'{SITE}/', 'logo': f'{SITE}/assets/art/logo-sic-owl.png',
          'description': 'A research network studying cities and regions as complex adaptive systems.',
          'founder': {'@type': 'Person', 'name': lead[0]['name'],
                      'affiliation': {'@type': 'CollegeOrUniversity', 'name': lead[0]['institution']}},
          'member': [person_ld(p) for p in fellows]}
region('jsonld', f'<script type="application/ld+json">{json.dumps(org_ld, ensure_ascii=False)}</script>')
open(idx_path, 'w').write(idx)

# ================================================================== sitemap, robots
today = datetime.date.today().isoformat()
urls = ['', 'people/', 'publications/', 'learn/', 'strange/', 'about/']
write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
      + ''.join(f'  <url><loc>{SITE}/{u}</loc><lastmod>{today}</lastmod></url>\n' for u in urls) + '</urlset>\n')
write('robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n')

print(f'built: {N_FELLOWS} fellows, {N_UNIS} universities, {N_COUNTRIES} countries; '
      f'{T["multi_fellow"]} multi-fellow works; masthead {N_MAST}')
