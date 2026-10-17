   
import os

from .. import lrc


def _from_tags(path):
                                                                     
    try:
        import mutagen
        f = mutagen.File(path)
    except Exception:
        return None
    tags = getattr(f, "tags", None)
    if tags is None:
        return None
    try:
        if hasattr(tags, "getall"):                            
            for frame in tags.getall("SYLT"):
                if getattr(frame, "format", 2) == 2 and frame.text:                      
                    return lrc.to_lrc([(ms / 1000.0, words.strip()) for words, ms in frame.text])
            for frame in tags.getall("USLT"):
                if frame.text and frame.text.strip():
                    return frame.text
            return None
        value = tags.get("\xa9lyr")                            
        if value:
            return str(value[0])
        for key in ("lyrics", "unsyncedlyrics", "syncedlyrics"):                     
            value = tags.get(key)
            if value:
                return "\n".join(str(v) for v in value)
    except Exception:
        pass
    return None


def _from_sidecar(path):
    folder, name = os.path.split(path)
    stem = os.path.splitext(name)[0]
    candidates = [
                                                                   
        os.path.join(folder, ".lyrics", stem + ".lrc"),
        os.path.join(folder, ".lyrics", stem + ".txt"),
                                                 
        os.path.join(folder, f".{stem}.lrc"),
        os.path.join(folder, f".{stem}.txt"),
                                                        
        os.path.join(folder, stem + ".lrc"),
        os.path.join(folder, stem + ".txt"),
    ]
    for p in candidates:
        try:
            with open(p, encoding="utf-8-sig", errors="replace") as fh:
                return fh.read()
        except OSError:
            continue
    return None


def load(path):
                                
    return lrc.parse(_from_tags(path) or _from_sidecar(path) or "")
