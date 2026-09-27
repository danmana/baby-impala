"""Bake a Spotify playlist into the "Real Deal" tape.

    python3 tools/fetch_playlist.py [playlist id]

Reads the playlist from Spotify's public embed page (no login needed) and
writes src/content/spotify-tape.json: title, artist, track id and length for
every track that has a 30-second preview, in playlist order. The embed page
lists the first 100 tracks of a playlist.

Default: "Supernatural Soundtrack [All Seasons]" by Solitude Collective.
"""
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PLAYLIST = sys.argv[1] if len(sys.argv) > 1 else '1IEQ8C3G1qT0W80muYgROT'
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36'}

html = urllib.request.urlopen(urllib.request.Request(f'https://open.spotify.com/embed/playlist/{PLAYLIST}', headers=UA)).read().decode()
data = json.loads(re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S).group(1))
entity = data['props']['pageProps']['state']['data']['entity']
tracks = []
for t in entity.get('trackList', []):
    if not t.get('uri', '').startswith('spotify:track:'):
        continue
    if not (t.get('audioPreview') or {}).get('url') or t.get('isPlayable') is False:
        continue
    tracks.append({
        'title': t['title'],
        'artist': t['subtitle'].replace(' ', ' '),
        'spotify': t['uri'].split(':')[-1],
        'seconds': round(t['duration'] / 1000),
    })
out = {
    'playlist': PLAYLIST,
    'name': entity.get('name') or entity.get('title'),
    'by': entity.get('subtitle'),
    'tracks': tracks,
}
path = os.path.join(ROOT, 'src', 'content', 'spotify-tape.json')
with open(path, 'w') as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
    f.write('\n')
print(f'{out["name"]} by {out["by"]}: {len(tracks)} playable tracks of {len(entity.get("trackList", []))} -> {os.path.relpath(path, ROOT)}')
