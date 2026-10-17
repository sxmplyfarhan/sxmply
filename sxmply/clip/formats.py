                                                                                      
import os
import sys
from dataclasses import dataclass

from .. import config, ui

                           
                                                                                        
AUDIO = {
    "mp3": ("mp3", True),
    "m4a": ("m4a", True),
    "opus": ("opus", True),
    "flac": ("flac", False),
    "wav": ("wav", False),
}
VIDEO = ("mp4", "mkv", "webm")

                                                                                          
AUDIO_QUALITY = [
    ("320", "320 kbps  (best, biggest)"),
    ("256", "256 kbps"),
    ("192", "192 kbps  (good for most music)"),
    ("128", "128 kbps  (smallest)"),
]
VIDEO_QUALITY = [
    ("best", "Best available  (biggest)"),
    ("1080", "1080p"),
    ("720", "720p"),
    ("480", "480p"),
    ("360", "360p  (smallest)"),
]

DEFAULT_AUDIO = ("mp3", "192")
DEFAULT_VIDEO = ("mp4", "best")


@dataclass
class Settings:
    audio: bool
    fmt: str
    quality: str                                                                             
    save_path: str
    lyrics: bool = True                                                         

    def describe(self):
        if self.audio:
            q = f" · {self.quality} kbps" if self.quality else " · lossless"
        else:
            q = " · best quality" if self.quality == "best" else f" · up to {self.quality}p"
        return f"{self.fmt.upper()}{q}"


def _index(options, value):
    for i, (v, _) in enumerate(options):
        if v == value:
            return i
    return 0


def _fail(msg):
    ui.error(msg)
    sys.exit(2)


def choose_settings(args, spotify=False):
\
\
                                                                           
    interactive = sys.stdin.isatty() and not args.y
    last = config.get("clip_last") or {}

                             
    if spotify or args.a:
        audio = True
    elif args.v:
        audio = False
    elif args.f and args.f.lower() in AUDIO:
        audio = True
    elif args.f and args.f.lower() in VIDEO:
        audio = False
    elif interactive:
        audio = ui.menu("What do you want?", ["Audio (music)", "Video"],
                        default=0 if last.get("audio", True) else 1) == 0
    else:
        audio = last.get("audio", True)

                         
    names = list(AUDIO) if audio else list(VIDEO)
    if args.f:
        fmt = args.f.lower()
        if fmt not in names:
            _fail(f"'{fmt}' isn't {'an audio' if audio else 'a video'} format. Choose from: {', '.join(names)}")
    else:
        fallback = (DEFAULT_AUDIO if audio else DEFAULT_VIDEO)[0]
        remembered = last.get("fmt") if last.get("audio", True) == audio else None
        default_fmt = remembered if remembered in names else fallback
        if interactive:
            fmt = names[ui.menu("File format", [n.upper() for n in names],
                                default=names.index(default_fmt))]
        else:
            fmt = default_fmt

                            
    if audio and not AUDIO[fmt][1]:
        quality = ""                                           
    else:
        options = AUDIO_QUALITY if audio else VIDEO_QUALITY
        if args.q:
            quality = args.q.lower()
            if quality != "best" and not quality.isdigit():
                _fail("-q takes a number (kbps for audio, height for video, e.g. 720) or 'best'.")
            if audio and quality == "best":
                quality = options[0][0]
        else:
            fallback = (DEFAULT_AUDIO if audio else DEFAULT_VIDEO)[1]
            remembered = last.get("quality") if last.get("audio", True) == audio else None
            default_q = remembered if remembered in dict(options) else fallback
            if interactive:
                title = "Quality (higher = bigger file)" if audio else "Quality / size (lower = smaller file)"
                quality = options[ui.menu(title, [label for _, label in options],
                                          default=_index(options, default_q))][0]
            else:
                quality = default_q

                           
    if args.D:
        save_path = config.resolve_dir(args.D)
    else:
        home = config.get("clip_dir")
        default_dir = home or os.getcwd()
        if interactive:
            print()
            save_path = config.resolve_dir(ui.ask_default("Save to", default_dir))
            if not home:
                ui.info("Tip: set a permanent folder with  sxmply clip home <folder>")
        else:
            save_path = default_dir

    settings = Settings(audio=audio, fmt=fmt, quality=quality, save_path=save_path,
                        lyrics=not getattr(args, "no_lyrics", False))
    config.set("clip_last", {"audio": audio, "fmt": fmt, "quality": quality})
    if interactive:
        ui.info(f"{settings.describe()}  →  {settings.save_path}")
    return settings
