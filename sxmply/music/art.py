\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
\
   
import base64
import concurrent.futures
import fcntl
import json
import os
import re
import select
import shutil
import struct
import subprocess
import sys
import tempfile
import termios
import threading
import time
from dataclasses import dataclass, field

MODES = ("auto", "kitty", "sixel", "ansi", "ascii", "off")
_IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")
_FOLDER_NAMES = ("cover", "folder", "front", "albumart", "album")
_KITTY_ID = 7


                                     
def cell_size():
                                                                                                   
    try:
        rows, cols, xpx, ypx = struct.unpack("HHHH", fcntl.ioctl(1, termios.TIOCGWINSZ, b"\0" * 8))
        if rows and cols and xpx and ypx:
            return max(xpx // cols, 1), max(ypx // rows, 1)
    except (OSError, ValueError):
        pass
    return 10, 20


def truecolor():
    return os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit")


def _probe(fd, timeout=0.5):
\
\
                                                                        
    sys.stdout.write("\033_Gi=31,s=1,v=1,a=q,t=d,f=24;AAAA\033\\\033[c")
    sys.stdout.flush()
    buf, end = b"", time.monotonic() + timeout
    while time.monotonic() < end:
        if not select.select([fd], [], [], max(end - time.monotonic(), 0))[0]:
            break
        try:
            buf += os.read(fd, 4096)
        except OSError:
            break
        if re.search(rb"\x1b\[\?[\d;]*c", buf):
            break
    text = buf.decode("latin-1")
    if "_Gi=31;OK" in text:
        return "kitty"
    m = re.search(r"\x1b\[\?([\d;]*)c", text)
    if m and "4" in m.group(1).split(";"):
        return "sixel"
    return None


def detect_mode(requested="auto", fd=None):
                                                                                        
    choice = requested if requested != "auto" else os.environ.get("SXMPLY_IMAGES", "auto").lower()
    if choice in MODES and choice != "auto":
        return choice
    if os.environ.get("NO_COLOR") or os.environ.get("TERM") == "dumb":
        return "ascii"
    term = os.environ.get("TERM", "")
    if os.environ.get("TMUX") or term.startswith(("screen", "tmux")):
        return "ansi"                                                                    
    if fd is not None:
        found = _probe(fd)
        if found:
            return found
    return "ansi"


                                 
def _run(cmd, data=None, timeout=20):
    try:
        r = subprocess.run(cmd, input=data, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                           timeout=timeout)
        return r.stdout if r.returncode == 0 else b""
    except (OSError, subprocess.SubprocessError):
        return b""


def _picture_stream(path):
                                                                                                 
    if not shutil.which("ffprobe"):
        return None
    out = _run(["ffprobe", "-v", "error", "-show_entries",
                "stream=index,codec_type:stream_disposition=attached_pic", "-of", "json", path], timeout=10)
    try:
        for s in json.loads(out or b"{}").get("streams", []):
            if s.get("codec_type") == "video" and s.get("disposition", {}).get("attached_pic"):
                return s["index"]
    except (ValueError, AttributeError):
        pass
    return None


def _mkv_attachment(path, tmpdir):
                                                                                  
    if os.path.splitext(path)[1].lower() != ".mkv":
        return None
    out = os.path.join(tmpdir, "attachment")
    _run(["ffmpeg", "-v", "quiet", "-y", "-dump_attachment:t:0", out, "-i", path], timeout=10)
    return out if os.path.exists(out) and os.path.getsize(out) > 0 else None


def _sidecar(path):
    folder, name = os.path.split(path)
    stem = os.path.splitext(name)[0]
    try:
        files = {f.lower(): f for f in os.listdir(folder or ".")}
    except OSError:
        return None
    for base in [stem.lower(), *_FOLDER_NAMES]:
        for ext in _IMAGE_EXTS:
            if base + ext in files:
                return os.path.join(folder, files[base + ext])
    return None


def _scale_filter(w, h):
    return f"crop='min(iw,ih)':'min(iw,ih)',scale={w}:{h}:flags=area"


def decode_cover(track, w, h, pix_fmt="rgb24"):
                                                                                             
    if not shutil.which("ffmpeg"):
        return None
    path = track.path
    vf = _scale_filter(w, h)
    tail = ["-frames:v", "1", "-vf", vf, "-f", "rawvideo", "-pix_fmt", pix_fmt, "-"]
    need = w * h * (1 if pix_fmt == "rgb8" else 3)
    attempts = []
    idx = _picture_stream(path)
    if idx is not None:
        attempts.append(["ffmpeg", "-v", "error", "-i", path, "-map", f"0:{idx}", *tail])
    with tempfile.TemporaryDirectory(prefix="sxmply-art-") as tmp:
        att = _mkv_attachment(path, tmp)
        if att:
            attempts.append(["ffmpeg", "-v", "error", "-i", att, *tail])
        side = _sidecar(path)
        if side:
            attempts.append(["ffmpeg", "-v", "error", "-i", side, *tail])
        if track.is_video:                                                               
            at = max(min(track.duration * 0.1, 60), 0) if track.duration else 5
            attempts.append(["ffmpeg", "-v", "error", "-ss", f"{at:.1f}", "-i", path,
                             "-map", "0:v:0", "-an", *tail])
            attempts.append(["ffmpeg", "-v", "error", "-i", path, "-map", "0:v:0", "-an", *tail])
        for cmd in attempts:
            data = _run(cmd)
            if len(data) == need:
                return data
    return None


                       
_RAMP = " .:-=+*#%@"


def _to_256(r, g, b):
    if r == g == b:
        if r < 8:
            return 16
        if r > 248:
            return 231
        return 232 + round((r - 8) / 247 * 24)
    return 16 + 36 * round(r / 255 * 5) + 6 * round(g / 255 * 5) + round(b / 255 * 5)


def ansi_lines(rgb, cols, rows, true_color):
                                                                                   
    stride = cols * 3
    lines = []
    for y in range(rows):
        parts, last = [], None
        for x in range(cols):
            t = (y * 2) * stride + x * 3
            b = (y * 2 + 1) * stride + x * 3
            top, bot = tuple(rgb[t:t + 3]), tuple(rgb[b:b + 3])
            if (top, bot) != last:
                if true_color:
                    parts.append(f"\033[38;2;{top[0]};{top[1]};{top[2]};48;2;{bot[0]};{bot[1]};{bot[2]}m")
                else:
                    parts.append(f"\033[38;5;{_to_256(*top)};48;5;{_to_256(*bot)}m")
                last = (top, bot)
            parts.append("▀")
        lines.append("".join(parts) + "\033[0m")
    return lines


def ascii_lines(rgb, cols, rows):
    lines = []
    for y in range(rows):
        row = []
        for x in range(cols):
            r, g, b = rgb[(y * cols + x) * 3:(y * cols + x) * 3 + 3]
            lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            row.append(_RAMP[min(int(lum * len(_RAMP)), len(_RAMP) - 1)])
        lines.append("".join(row))
    return lines


def kitty_payload(rgb, px_w, px_h, cols, rows):
\
                                                                                   
    data = base64.standard_b64encode(rgb).decode("ascii")
    chunks = [data[i:i + 4096] for i in range(0, len(data), 4096)] or [""]
    out = [f"\033_Ga=d,d=I,i={_KITTY_ID},q=2\033\\"]
    for n, chunk in enumerate(chunks):
        more = 1 if n < len(chunks) - 1 else 0
        ctrl = (f"a=T,f=24,s={px_w},v={px_h},c={cols},r={rows},i={_KITTY_ID},C=1,q=2,m={more}"
                if n == 0 else f"q=2,m={more}")
        out.append(f"\033_G{ctrl};{chunk}\033\\")
    return "".join(out)


KITTY_DELETE = f"\033_Ga=d,d=I,i={_KITTY_ID},q=2\033\\"


def sixel_payload(pixels, w, h):
                                                                                                
    out = ["\033Pq", f'"1;1;{w};{h}']
    used = sorted(set(pixels))
    for c in used:                                                                       
        r, g, b = (c >> 5) & 7, (c >> 2) & 7, c & 3
        out.append(f"#{c};2;{r * 100 // 7};{g * 100 // 7};{b * 100 // 3}")
    for top in range(0, h, 6):
        bands = {}
        for x in range(w):
            for dy in range(min(6, h - top)):
                c = pixels[(top + dy) * w + x]
                row = bands.get(c)
                if row is None:
                    row = bands[c] = bytearray(w)
                row[x] |= 1 << dy
        for c, row in bands.items():
            out.append(f"#{c}")
            x = 0
            while x < w:                                                       
                run = 1
                while x + run < w and row[x + run] == row[x]:
                    run += 1
                ch = chr(63 + row[x])
                out.append(f"!{run}{ch}" if run > 3 else ch * run)
                x += run
            out.append("$")
        out.append("-")
    out.append("\033\\")
    return "".join(out)


                                         
@dataclass
class Spec:
                                                                                         
    mode: str
    cols: int
    rows: int
    cell_w: int
    cell_h: int
    true_color: bool

    def key(self):
        return (self.mode, self.cols, self.rows, self.cell_w, self.cell_h, self.true_color)


@dataclass
class Rendered:
    found: bool = False
    lines: list = field(default_factory=list)                                     
    payload: str = ""                                                                                  


def render(track, spec):
    if spec.mode == "off" or spec.cols < 2 or spec.rows < 1:
        return Rendered()
    if spec.mode in ("ansi", "ascii"):
        pw, ph = spec.cols, spec.rows * 2 if spec.mode == "ansi" else spec.rows
        rgb = decode_cover(track, pw, ph)
        if rgb is None:
            return Rendered()
        if spec.mode == "ansi":
            return Rendered(True, ansi_lines(rgb, spec.cols, spec.rows, spec.true_color))
        return Rendered(True, ascii_lines(rgb, spec.cols, spec.rows))
    if spec.mode == "kitty":
        px = min(max(spec.cols * spec.cell_w, spec.rows * spec.cell_h), 400)
        rgb = decode_cover(track, px, px)
        return Rendered(True, payload=kitty_payload(rgb, px, px, spec.cols, spec.rows)) if rgb else Rendered()
                                                                 
    w, h = spec.cols * spec.cell_w, spec.rows * spec.cell_h
    pix = decode_cover(track, w, h, "rgb8")
    return Rendered(True, payload=sixel_payload(pix, w, h)) if pix else Rendered()


class ArtLoader:
                                                                                       

    def __init__(self):
        self._pool = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="art")
        self._jobs = {}
        self._lock = threading.Lock()

    def get(self, track, spec):
                                                                                         
        key = (track.path, spec.key())
        with self._lock:
            job = self._jobs.get(key)
            if job is None:
                if len(self._jobs) > 24:                                                        
                    self._jobs.pop(next(iter(self._jobs)))
                job = self._jobs[key] = self._pool.submit(self._safe, track, spec)
        return job.result() if job.done() else None

    @staticmethod
    def _safe(track, spec):
        try:
            return render(track, spec)
        except Exception:
            return Rendered()

    def close(self):
        self._pool.shutdown(wait=False, cancel_futures=True)
