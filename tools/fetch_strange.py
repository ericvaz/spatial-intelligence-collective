"""Fetch the essays STRANGE has published on Substack into content/strange.json.

The magazine publishes one piece at a time at strangemagazine.substack.com. Every post
there is written under the STRANGE Magazine account, with the real author in the subtitle
("By A. Stewart Fotheringham"), so the author is read from the subtitle.

Run by the "STRANGE feed" GitHub workflow every few hours, then tools/build_site.py.
The file is only rewritten when the list of essays changes, so an unchanged feed leaves
no diff and no commit.
"""
import datetime
import email.utils
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

FEED = 'https://strangemagazine.substack.com/feed'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'content', 'strange.json')
TZ = ZoneInfo('America/Toronto')
BY = re.compile(r'^\s*by\s+(.+?)\s*$', re.I)


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'spatialintelligence.network site builder'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def posts_from(xml):
    root = ET.fromstring(xml)
    dc = '{http://purl.org/dc/elements/1.1/}creator'
    out = []
    for item in root.iter('item'):
        title = (item.findtext('title') or '').strip()
        link = (item.findtext('link') or '').strip()
        if not title or not link:
            continue
        sub = (item.findtext('description') or '').strip()
        m = BY.match(sub)
        author = m.group(1) if m else (item.findtext(dc) or '').strip()
        if author == 'STRANGE Magazine':
            author = ''
        date = email.utils.parsedate_to_datetime(item.findtext('pubDate')).astimezone(TZ).date().isoformat()
        out.append({'title': title, 'author': author, 'url': link.split('?')[0], 'date': date})
    out.sort(key=lambda p: p['date'], reverse=True)
    return out


def main():
    try:
        posts = posts_from(fetch(FEED))
    except Exception as e:  # keep the last good list if Substack is unreachable; try again next run
        print(f'::warning::STRANGE feed not updated: {e}')
        return
    old = json.load(open(OUT)) if os.path.exists(OUT) else {}
    if old.get('posts') == posts:
        print(f'STRANGE feed unchanged ({len(posts)} essays)')
        return
    data = {'source': FEED, 'updated': datetime.date.today().isoformat(), 'posts': posts}
    with open(OUT, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(f'STRANGE feed updated: {len(posts)} essays')


if __name__ == '__main__':
    main()
