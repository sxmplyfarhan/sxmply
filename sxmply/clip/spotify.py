\
\
\
\
\
   
import json
import re
import urllib.request

EMBED_CAP_HINT = 100                                    

_LINK_RE = re.compile(r"open\.spotify\.com/(?:intl-[a-z]+/)?(playlist|album|track)/([A-Za-z0-9]+)")
_NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.S)
_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


class SpotifyError(Exception):
    pass


def parse_link(link):
    m = _LINK_RE.search(link)
    return (m.group(1), m.group(2)) if m else None


def is_spotify_link(link):
    return parse_link(link) is not None


def _tracks_from_entity(entity):
    items = entity.get("trackList")
    if items is None:                  
        items = [entity]
    tracks = []
    for t in items:
        title = t.get("title") or t.get("name")
        artist = t.get("subtitle") or ""
        if not artist and t.get("artists"):
            artist = t["artists"][0].get("name", "")
        artist = artist.replace("\xa0", " ").split(",")[0].strip()
        if title:
            tracks.append(f"{title} {artist}".strip())
    return tracks


def fetch_tracks(link):
    kind, spotify_id = parse_link(link)
    req = urllib.request.Request(
        f"https://open.spotify.com/embed/{kind}/{spotify_id}",
        headers={"User-Agent": _UA},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", "replace")
    except OSError as e:
        raise SpotifyError(f"couldn't reach Spotify ({e}). Is the link public?")

    m = _NEXT_DATA_RE.search(html)
    if not m:
        raise SpotifyError("Spotify's page layout wasn't recognised (it may have changed).")
    try:
        entity = json.loads(m.group(1))["props"]["pageProps"]["state"]["data"]["entity"]
        tracks = _tracks_from_entity(entity)
    except (KeyError, TypeError, ValueError) as e:
        raise SpotifyError(f"couldn't read the track list ({e!r}).")

    if not tracks:
        raise SpotifyError("no tracks found. The playlist may be empty or private.")
    return tracks
