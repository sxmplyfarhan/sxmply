                                                       
import sys

import yt_dlp

from .. import ui

RESULTS = 5


def search_and_select(query=""):
                                                                                  
    query = query.strip() or ui.ask("Search YouTube for")
    if not query:
        ui.info("No query given, exiting.")
        sys.exit(0)

    opts = {"quiet": True, "no_warnings": True, "extract_flat": True,
            "skip_download": True, "noplaylist": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"ytsearch{RESULTS}:{query}", download=False)
    entries = [e for e in (info.get("entries") or []) if e]
    if not entries:
        ui.warn("No results found.")
        sys.exit(0)

    ui.heading(f"Top {len(entries)} results")
    for idx, entry in enumerate(entries, 1):
        print(f"  {ui.paint(idx, 'cyan')}. {entry.get('title')} "
              f"{ui.paint('(' + str(entry.get('url')) + ')', 'gray')}")

    while True:
        choice = ui.ask(f"Choose a video (1-{len(entries)}) or 'q' to cancel").lower()
        if choice == "q":
            ui.info("Canceled.")
            sys.exit(0)
        if choice.isdigit() and 1 <= int(choice) <= len(entries):
            return entries[int(choice) - 1]["url"]
        ui.warn(f"Enter 1-{len(entries)} or 'q'.")
