\
\
\
\
   
import difflib
import importlib
import sys

from . import __version__, ui

                                                                           
COMMANDS = {
    "clip": ("sxmply.clip.cli", "download music & video from YouTube, Spotify and more"),
    "music": ("sxmply.music.cli", "terminal music player for your own songs"),
}


def print_help():
    ui.banner()
    print("\nUsage: sxmply <command> [options]\n")
    print("Commands:")
    for name, (_, desc) in COMMANDS.items():
        print(f"  {ui.paint(name.ljust(8), 'cyan', 'bold')} {desc}")
    print("\nRun 'sxmply <command> --help' for help on a command.")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    if not argv or argv[0] in ("-h", "--help", "help"):
        print_help()
        return
    if argv[0] in ("-V", "--version"):
        print(f"sxmply {__version__}")
        return

    name = argv[0]
    if name not in COMMANDS:
        ui.error(f"Unknown command '{name}'.")
        close = difflib.get_close_matches(name, COMMANDS, n=1)
        if close:
            ui.info(f"Did you mean: sxmply {close[0]}")
        print_help()
        sys.exit(2)

                                                                                          
    importlib.import_module(COMMANDS[name][0]).main(argv[1:])
