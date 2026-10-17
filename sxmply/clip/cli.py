                                                        
import argparse
import os
import sys

from .. import config, ui
from . import downloader, formats, search, spotify

LEGAL = """\
Legal notice: this tool is for personal use only. Downloading from YouTube,
Spotify or other sites may violate their Terms of Service and/or copyright law
in your country. Use it responsibly and don't distribute downloaded content.
The author is not responsible for any misuse or legal consequences."""

EPILOG = """\
examples:
  sxmply clip https://youtu.be/LgPEyGlUQH8              (asks format, quality, folder)
  sxmply clip https://youtu.be/LgPEyGlUQH8 -a -f flac   (audio, FLAC, no questions about it)
  sxmply clip https://youtu.be/LgPEyGlUQH8 -f mp4 -q 720 -y
  sxmply clip https://open.spotify.com/playlist/XXXXXXXX -D ~/Music
  sxmply clip search                   (asks what to search for)
  sxmply clip search lofi hip hop      (searches straight away)
  sxmply clip home ~/Music             (always save here unless told otherwise)
  sxmply clip home                     (show the current folder)
  sxmply clip home --reset             (forget it, reset to ~/.config/sxmply/clip)

notes:
  - Anything you don't give as an option is asked, so you can just paste a link.
    -y skips every question and uses your last choice (or MP3 192 / MP4 best).
  - Audio formats: mp3, m4a, opus, flac, wav. Video formats: mp4, mkv, webm.
  - Quality is the size knob: -q is kbps for audio (320/256/192/128) and the
    maximum height for video (1080/720/480/360 or 'best').
  - Audio files get cover art, title, artist, album, year and lyrics (synchronized when
    available, from lrclib.net) written into them. --no-lyrics skips the lyrics lookup.
    Formats that can't hold a cover (WAV, WEBM) get a .jpg next to the file instead.
  - Works with any site yt-dlp supports, not only YouTube.
  - Spotify links need no login. They are matched on YouTube (audio only).
    Only public playlists/albums/tracks work.
""" + "\n" + LEGAL


def build_parser():
    p = argparse.ArgumentParser(
        prog="sxmply clip",
        usage=("sxmply clip [-a | -v] [-f FORMAT] [-q QUALITY] [-D DIR] [-y] <link | search [words ...]>\n"
               "       sxmply clip home [DIR | --reset]"),
        description="Download music or videos from YouTube, Spotify and many other sites.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("target", nargs="*", metavar="link | search | home",
                   help="a URL to download, 'search' (optionally followed by what to look for), "
                        "or 'home' to show/set the folder downloads go to")
    kind = p.add_mutually_exclusive_group()
    kind.add_argument("-a", action="store_true", help="audio only (MP3); always used for Spotify")
    kind.add_argument("-v", action="store_true", help="video (MP4); this is the default")
    p.add_argument("-f", metavar="FORMAT", help="file format: mp3 m4a opus flac wav | mp4 mkv webm")
    p.add_argument("-q", metavar="QUALITY", help="kbps for audio, max height for video (or 'best')")
    p.add_argument("-D", metavar="DIR", help="output directory (skips the 'save to' question)")
    p.add_argument("-y", "--yes", dest="y", action="store_true",
                   help="don't ask anything: use the options given, else your last choice")
    p.add_argument("--no-lyrics", dest="no_lyrics", action="store_true",
                   help="don't look up lyrics online (tags and cover art are still added)")
    p.add_argument("--reset", action="store_true", help="with 'home': go back to the default folder")
    return p


def download_many(items, settings):
                                                                            
    failed = []
    for n, (label, link) in enumerate(items, 1):
        ui.heading(f"[{n}/{len(items)}] {label}")
        if not downloader.download(link, settings):
            failed.append(label)

    where = os.path.abspath(settings.save_path)
    done = len(items) - len(failed)
    print()
    if done:
        ui.success(f"{done}/{len(items)} saved to {where}")
    if failed:
        ui.warn("These failed:")
        for label in failed:
            print(f"  - {label}")


def run_spotify(link, args):
    ui.info("Reading Spotify link…")
    try:
        tracks = spotify.fetch_tracks(link)
    except spotify.SpotifyError as e:
        ui.error(f"Couldn't read the Spotify link: {e}")
        sys.exit(1)

    ui.heading(f"Found {len(tracks)} track(s)")
    ui.preview(tracks[:5], len(tracks))
    if len(tracks) >= spotify.EMBED_CAP_HINT:
        ui.warn("Spotify's public page stops at ~100 tracks, so a longer playlist may be cut off.")

    n = ui.choose_count(len(tracks), "tracks") if len(tracks) > 1 else 1
    items = [(t, f"ytsearch1:{t}") for t in tracks[:n]]
    settings = formats.choose_settings(args, spotify=True)
    download_many(items, settings)


def run_generic(link, args):
    info = downloader.get_playlist_info(link)
    if info is None:
        sys.exit(1)

    if info["total"] > 0:
        ui.heading(f"Playlist: {info['title'] or info['id']}")
        ui.preview(info["titles"], info["total"])
        n = ui.choose_count(info["total"], "videos")
        items = [(e.get("title") or "(untitled)", downloader.entry_url(e))
                 for e in info["entries"][:n] if downloader.entry_url(e)]
        settings = formats.choose_settings(args)
        download_many(items, settings)
    else:
        if info["title"]:
            ui.info(f"Found: {info['title']}")
        settings = formats.choose_settings(args)
        download_many([(info["title"] or link, link)], settings)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    literal = []
    if "--" in argv:
        cut = argv.index("--")
        argv, literal = argv[:cut], argv[cut + 1:]
    args = parser.parse_intermixed_args(argv)
    args.target = args.target + literal

    if not args.target:
        ui.banner("clip", "download music & video")
        parser.print_help()
        return

    first, rest = args.target[0], args.target[1:]
    if first == "home":                                    
        config.home_command("clip", "download_dir", rest, "download", "sxmply clip home",
                            create=True, reset=args.reset)
        return
    if first != "search" and rest:
        parser.error("give one link at a time (or use: search <words>)")

    try:
        ui.banner("clip", "download music & video")
        if first == "search":
            link = search.search_and_select(" ".join(rest))
        else:
            link = first

        if spotify.is_spotify_link(link):
            run_spotify(link, args)
        else:
            run_generic(link, args)

    except (KeyboardInterrupt, EOFError):
        print()
        ui.warn("Canceled.")
        sys.exit(0)