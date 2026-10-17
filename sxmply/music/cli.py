                                                                 
import argparse
import os
import sys

from .. import config, ui

EPILOG = """\
examples:
  sxmply music                         play your music folder
  sxmply music ~/Music/Jazz            play a folder (sub-folders included)
  sxmply music song.mp3 other.flac     play specific files
  sxmply music -s -r all               start shuffled, repeating everything
  sxmply music -F                      only your favorites
  sxmply music home ~/Music            remember your music folder
  sxmply music home                    show the remembered folder
  sxmply music home --reset            reset back to ~/.config/sxmply/music

keys inside the player (press ? there for the full list):
  space pause · n/b next/previous · ←/→ seek · enter play
  P playlists · a add to playlist · f favorite · l lyrics · ? help · q quit

notes:
  - Needs mpv (sound engine). Tags, lyrics and cover art are read from files.
  - Cover art is drawn with Kitty/Sixel graphics protocol, else coloured blocks.
  - Default music directory is ~/.config/sxmply/music unless changed with 'music home'.
  - Custom keybinds and theme colors can be edited in ~/.config/sxmply/music/config.json.
"""


def default_dir():
                                                                                     
    return config.get("music_dir", tool="music") or config.default_dir("music")


def art_modes():
    return ("auto", "kitty", "sixel", "ansi", "ascii", "off")


def build_parser():
    p = argparse.ArgumentParser(
        prog="sxmply music",
        usage=("sxmply music [-s] [-r {off,all,one}] [-F] [--no-recursive] [--images MODE] [--list] [folder | file ...]\n"
               "       sxmply music home [DIR | --reset]"),
        description="Terminal music player for your local files (mp3, flac, m4a, ogg, opus, wav, mp4, webm ...).",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("paths", nargs="*", metavar="folder | file",
                   help="what to play (default: your music folder)")
    p.add_argument("-s", "--shuffle", action="store_true", help="start with shuffle on")
    p.add_argument("-r", "--repeat", choices=("off", "all", "one"), default="off",
                   help="start with this repeat mode")
    p.add_argument("-F", "--favorites", action="store_true", help="only show favorites (♥)")
    p.add_argument("--no-recursive", action="store_true", help="don't look inside sub-folders")
    p.add_argument("--images", choices=art_modes(), default="auto", metavar="MODE",
                   help="how to draw cover art: auto, kitty, sixel, ansi, ascii or off "
                        "(auto asks your terminal; env var SXMPLY_IMAGES works too)")
    p.add_argument("--list", action="store_true", help="print the songs found and exit")
    return p


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    if argv and argv[0] in ("home", "folder"):                                             
        rest = argv[1:]
        reset = "--reset" in rest
        config.home_command("music", "music_dir", [a for a in rest if a != "--reset"], "music",
                            "sxmply music home", create=False, reset=reset)
        return

    args = build_parser().parse_args(argv)

    if os.name == "nt":
        ui.error("sxmply music works on Linux and macOS for now.")
        sys.exit(1)

    paths = args.paths or [default_dir()]
    if not args.paths and not os.path.isdir(paths[0]):
        ui.error(f"No music folder found ({paths[0]}).")
        ui.info("Point me at one with:  sxmply music home <folder>")
        sys.exit(1)

    from . import library
    tracks = library.find_tracks(paths, recursive=not args.no_recursive)
    if not tracks:
        ui.error("No songs found in: " + ", ".join(paths))
        ui.info("Playable files: " + " ".join(sorted(library.EXTENSIONS)))
        ui.info("Tip: place songs in " + paths[0] + " or run: sxmply music home <your_music_folder>")
        sys.exit(1)

    if args.list:
        for i, t in enumerate(tracks, 1):
            print(f"{i:>4}. {t.path}")
        return

    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        ui.error("The player needs an interactive terminal. (Use --list to print the songs instead.)")
        sys.exit(1)

    from .app import MusicApp
    from .player import PlayerError

    app = MusicApp(tracks, shuffle=args.shuffle, repeat=args.repeat, favorites_only=args.favorites,
                   roots=paths, images=args.images)
    if args.favorites and not app.view:
        ui.warn("You have no favorites in these songs yet. Press f in the player to add some.")
        app.fav_only = False
        app.refresh_view()

    ui.info(f"Found {len(tracks)} song(s). Starting player…")
    try:
        app.run()
    except PlayerError as e:
        ui.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        pass