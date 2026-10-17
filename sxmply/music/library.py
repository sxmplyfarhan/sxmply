                                                 
import os
import re
import threading
from dataclasses import dataclass

                                                                               
EXTENSIONS = {
    ".mp3", ".flac", ".m4a", ".ogg", ".opus", ".wav", ".aac", ".wma", ".ape",
    ".webm", ".mp4", ".mkv",
}


VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm"}


@dataclass(eq=False)
class Track:
    path: str
    title: str
    artist: str = ""
    album: str = ""
    year: str = ""
    duration: float = 0.0                              

    @property
    def is_video(self):
        return os.path.splitext(self.path)[1].lower() in VIDEO_EXTENSIONS

    @property
    def haystack(self):
        return f"{self.title} {self.artist} {self.album} {os.path.basename(self.path)}".lower()


def clean(text):
                                                                                           
    return " ".join(str(text).split())


def _natural(text):
    return [int(p) if p.isdigit() else p for p in re.split(r"(\d+)", text.lower())]


def find_tracks(paths, recursive=True):
                                                                                         
    found, seen = [], set()

    def add(path):
        path = os.path.abspath(path)
        if path in seen or os.path.splitext(path)[1].lower() not in EXTENSIONS:
            return
        seen.add(path)
        stem = os.path.splitext(os.path.basename(path))[0]
        found.append(Track(path=path, title=clean(stem) or stem))

    for raw in paths:
        p = os.path.expanduser(raw)
        if os.path.isfile(p):
            add(p)
        elif os.path.isdir(p):
            batch = []
            for root, dirs, files in os.walk(p):
                dirs[:] = sorted((d for d in dirs if not d.startswith(".")), key=_natural)
                if not recursive:
                    dirs[:] = []
                batch.extend(os.path.join(root, f) for f in files if not f.startswith("."))
            for f in sorted(batch, key=lambda x: _natural(os.path.relpath(x, p))):
                add(f)
    return found


def read_tags(track):
\
                                                                
    try:
        import mutagen
        f = mutagen.File(track.path, easy=True)
    except Exception:
        return
    if f is None:
        return
    try:
        if f.info and getattr(f.info, "length", 0):
            track.duration = float(f.info.length)
        tags = f.tags or {}
        def first(key):
            v = tags.get(key)
            return clean(v[0]) if v else ""
        track.title = first("title") or track.title
        track.artist = first("artist")
        track.album = first("album")
        track.year = first("date")[:4]
    except Exception:
        pass


def read_tags_in_background(tracks):
                                                                                             
    t = threading.Thread(target=lambda: [read_tags(x) for x in tracks], daemon=True)
    t.start()
    return t
