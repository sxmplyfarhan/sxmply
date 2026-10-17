
   
import bisect
import re
from dataclasses import dataclass, field

_TIME = re.compile(r"\[(\d{1,3}):(\d{1,2})(?:[.:](\d{1,3}))?\]")
_META = re.compile(r"^\s*\[([a-zA-Z#]+):([^\]]*)\]\s*$")
_WORD_TAG = re.compile(r"<\d{1,3}:\d{1,2}(?:[.:]\d{1,3})?>")                                       


@dataclass
class Lyrics:
    synced: bool
    lines: list = field(default_factory=list)                               
    times: list = field(default_factory=list)                                      

    def index_at(self, position):
                                                                                            
        if not self.synced:
            return -1
        return bisect.bisect_right(self.times, position) - 1


def looks_synced(text):
    return bool(text) and _TIME.search(text) is not None


def parse(text):
                                                                  
    if not text or not text.strip():
        return None
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    if not looks_synced(text):
        lines = [(None, ln.rstrip()) for ln in text.split("\n")]
        while lines and not lines[0][1].strip():                                    
            lines.pop(0)
        while lines and not lines[-1][1].strip():
            lines.pop()
        return Lyrics(False, lines) if lines else None

    offset = 0.0
    timed = []
    for raw in text.split("\n"):
        meta = _META.match(raw)
        if meta and not _TIME.match(raw):
            if meta.group(1).lower() == "offset":
                try:
                    offset = int(meta.group(2).strip()) / 1000.0
                except ValueError:
                    pass
            continue
        stamps = list(_TIME.finditer(raw))
        if not stamps:
            continue
        words = _WORD_TAG.sub("", raw[stamps[-1].end():]).strip()
        for m in stamps:
            minutes, seconds, frac = int(m.group(1)), int(m.group(2)), m.group(3) or "0"
            t = minutes * 60 + seconds + int(frac) / (10 ** len(frac))
            timed.append((max(t - offset, 0.0), words))                                         
    if not timed:
        return None
    timed.sort(key=lambda x: x[0])
    return Lyrics(True, timed, [t for t, _ in timed])


def to_lrc(lines):
                                        
    out = []
    for t, words in lines:
        cs = int(round(t * 100))
        out.append(f"[{cs // 6000:02d}:{(cs // 100) % 60:02d}.{cs % 100:02d}]{words}")
    return "\n".join(out)
