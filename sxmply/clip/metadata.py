
   
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from .. import lrc, ui

LRCLIB = "https://lrclib.net/api"
_UA = "sxmply (https://github.com/sxmplyfarhan/Clip-Command)"

                                                                                                
_NOISE = re.compile(
    r"\s*[\(\[][^\)\]]*\b(official|lyrics?|audio|video|visuali[sz]er|remaster(?:ed)?|hd|hq|4k|mv)\b[^\)\]]*[\)\]]",
    re.I)
_CHANNEL_SUFFIX = re.compile(r"\s*(?:[-–]\s*Topic|VEVO)\s*$", re.I)
_ARTIST_TITLE = re.compile(r"^(.+?)\s+[-–—]\s+(.+)$")

                                                     
EMBED_COVER = {"mp3", "m4a", "opus", "flac", "mp4", "mkv"}                                         
TAG_WITH_MUTAGEN = {"mp3", "m4a", "mp4", "flac", "opus", "wav"}


@dataclass
class Tags:
    title: str = ""
    artist: str = ""
    album: str = ""
    year: str = ""
    duration: float = 0.0


def _strip_noise(text):
    return _NOISE.sub("", text or "").strip()


def guess_tags(info):

                                                                                        
    title = _strip_noise(info.get("track") or info.get("title") or "")
    artist = (info.get("artist") or info.get("creator") or "").strip()
    if isinstance(info.get("artists"), list) and not artist:
        artist = ", ".join(str(a) for a in info["artists"])

    if artist:
        first = artist.split(",")[0].strip().lower()
        if title.lower().startswith(first + " - "):                                             
            title = title[len(first) + 3:].strip()
    elif not info.get("track"):
        m = _ARTIST_TITLE.match(title)
        if m:
            artist, title = m.group(1).strip(), m.group(2).strip()
    if not artist:
        artist = _CHANNEL_SUFFIX.sub("", info.get("channel") or info.get("uploader") or "").strip()

    year = str(info.get("release_year") or "")
    if not year:
                                                                                             
        year = str(info.get("release_date") or info.get("upload_date") or "")[:4]
    if not re.fullmatch(r"\d{4}", year):
        year = ""

    return Tags(title=title, artist=artist, album=(info.get("album") or "").strip(),
                year=year, duration=float(info.get("duration") or 0))


                             
def _get(path, params):
    url = f"{LRCLIB}/{path}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


def _best(results, duration):
                                                                                      
    usable = [r for r in results if isinstance(r, dict) and not r.get("instrumental")
              and (r.get("syncedLyrics") or r.get("plainLyrics"))]
    if not usable:
        return None
    if duration:
                                                                                       
        close = [r for r in usable if abs(float(r.get("duration") or 0) - duration) <= 15]
        if close:
            usable = close
        usable.sort(key=lambda r: (not r.get("syncedLyrics"), abs(float(r.get("duration") or 0) - duration)))
    else:
        usable.sort(key=lambda r: not r.get("syncedLyrics"))
    return usable[0]


def fetch_lyrics(tags):
                                                                                             
    if not tags.title:
        return None, False
    try:
        data = None
        if tags.artist and tags.album and tags.duration:                                   
            try:
                data = _get("get", {"track_name": tags.title, "artist_name": tags.artist,
                                    "album_name": tags.album, "duration": int(round(tags.duration))})
            except urllib.error.HTTPError as e:
                if e.code != 404:
                    raise
        if not isinstance(data, dict) or data.get("instrumental"):
            params = {"track_name": tags.title}
            if tags.artist:
                params["artist_name"] = tags.artist
            found = _get("search", params)
            data = _best(found, tags.duration) if isinstance(found, list) else None

                                                                                               
        if (not isinstance(data, dict) or not (data.get("syncedLyrics") or data.get("plainLyrics"))) and tags.artist:
            found = _get("search", {"q": f"{tags.title} {tags.artist}"})
            data = _best(found, tags.duration) if isinstance(found, list) else None
    except (OSError, ValueError):                                                             
        return None, False

    if not isinstance(data, dict):
        return None, False
    synced = (data.get("syncedLyrics") or "").strip()
    if synced:
        return synced, True
    plain = (data.get("plainLyrics") or "").strip()
    return (plain, False) if plain else (None, False)


                                     
def _write_id3(path, tags, text, synced):
    from mutagen.id3 import ID3, ID3NoHeaderError, SYLT, TALB, TDRC, TIT2, TPE1, USLT
    try:
        id3 = ID3(path)
    except ID3NoHeaderError:
        id3 = ID3()
    for frame, value, cls in (("TIT2", tags.title, TIT2), ("TPE1", tags.artist, TPE1),
                              ("TALB", tags.album, TALB), ("TDRC", tags.year, TDRC)):
        if value:
            id3.setall(frame, [cls(encoding=3, text=value)])
    if text:
        id3.setall("USLT", [USLT(encoding=3, lang="eng", desc="", text=text)])
        parsed = lrc.parse(text) if synced else None
        if parsed and parsed.synced:
            id3.setall("SYLT", [SYLT(encoding=3, lang="eng", format=2, type=1, desc="",
                                     text=[(words, int(t * 1000)) for t, words in parsed.lines])])
    id3.save(path)                                                                    


def _write_mp4(path, tags, text, synced):
    from mutagen.mp4 import MP4
    f = MP4(path)
    if f.tags is None:
        f.add_tags()
    for key, value in (("\xa9nam", tags.title), ("\xa9ART", tags.artist),
                       ("\xa9alb", tags.album), ("\xa9day", tags.year), ("\xa9lyr", text)):
        if value:
            f.tags[key] = [value]
    f.save()


def _write_vorbis(path, tags, text, synced):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".flac":
        from mutagen.flac import FLAC as Cls
    else:
        from mutagen.oggopus import OggOpus as Cls
    f = Cls(path)
    for key, value in (("title", tags.title), ("artist", tags.artist), ("album", tags.album),
                       ("date", tags.year), ("lyrics", text)):
        if value:
            f[key] = [value]
    f.save()


def _write_wav(path, tags, text, synced):
    from mutagen.wave import WAVE
    f = WAVE(path)
    if f.tags is None:
        f.add_tags()
    from mutagen.id3 import TALB, TDRC, TIT2, TPE1, USLT
    for cls, value in ((TIT2, tags.title), (TPE1, tags.artist), (TALB, tags.album), (TDRC, tags.year)):
        if value:
            f.tags.setall(cls.__name__, [cls(encoding=3, text=value)])
    if text:
        f.tags.setall("USLT", [USLT(encoding=3, lang="eng", desc="", text=text)])
    f.save()


_WRITERS = {"mp3": _write_id3, "m4a": _write_mp4, "mp4": _write_mp4,
            "flac": _write_vorbis, "opus": _write_vorbis, "wav": _write_wav}


def _write_sidecar(path, text, synced):
                                                                              
    folder, filename = os.path.split(path)
    stem = os.path.splitext(filename)[0]
    lyrics_dir = os.path.join(folder, ".lyrics")
    try:
        os.makedirs(lyrics_dir, exist_ok=True)
        side = os.path.join(lyrics_dir, stem + (".lrc" if synced else ".txt"))
        with open(side, "w", encoding="utf-8") as f:
            f.write(text.rstrip() + "\n")
        return side
    except OSError:
        return None


def finalize(path, info, settings):
                                                                                      
    try:
        tags = guess_tags(info)
        ext = os.path.splitext(path)[1].lstrip(".").lower()

        text, synced = (None, False)
                                                          
        if settings.lyrics:
            ui.info("Looking for lyrics…")
            text, synced = fetch_lyrics(tags)

        notes = []
        writer = _WRITERS.get(ext)
        if writer:
            try:
                writer(path, tags, text, synced)
            except ImportError:
                ui.warn("mutagen isn't installed, so tags and lyrics weren't written. Run ./install.sh.")
            except Exception as e:
                ui.warn(f"Couldn't write tags ({e}).")

        if text:
                                                                        
            _write_sidecar(path, text, synced)
            notes.append("synced lyrics" if synced else "lyrics")
        elif settings.lyrics:
            notes.append("no lyrics found")

        if info.get("thumbnail") or info.get("thumbnails"):
            notes.append("cover art embedded" if ext in EMBED_COVER
                         else "cover art saved next to the file")
        label = " – ".join(x for x in (tags.artist, tags.title) if x)
        ui.success(f"{label or os.path.basename(path)}" + (f"  ({', '.join(notes)})" if notes else ""))
    except Exception as e:                                                                            
        ui.warn(f"Downloaded, but couldn't finish tagging ({e}).")
