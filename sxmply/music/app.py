                                                                                  
import json
import math
import os
import random
import re
import shutil
import socket
import struct
import sys
import tempfile
import threading
import time
import unicodedata
from dataclasses import dataclass

from .. import config, ui
from . import art, keys, library, lyrics
from .player import MpvPlayer
from .playlist import Queue

ENTER_SCREEN = "\033[?1049h\033[?25l\033[?7l"
LEAVE_SCREEN = "\033[?7h\033[?25h\033[?1049l"
SLEEP_CHOICES = (0, 15, 30, 45, 60, 90)
SEEK_SMALL, SEEK_BIG = 5, 30
BAR_CHAR, EMPTY_CHAR = "█", "░"

_ANSI_RE = re.compile(r"\033\[[0-9;]*[a-zA-Z]")
DISCORD_CLIENT_ID = "1107328005374828605"

DEFAULT_THEME = {
    "primary": "magenta",
    "accent": "cyan",
    "playing": "green",
    "cursor": "reverse",
    "dim": "gray",
    "highlight": "yellow",
    "heart": "magenta",
}

DEFAULT_KEYBINDS = {
    "play_pause": ["space", " ", "p"],
    "next": ["n"],
    "prev": ["b"],
    "seek_forward": ["right"],
    "seek_backward": ["left"],
    "seek_forward_large": ["S-right"],
    "seek_backward_large": ["S-left"],
    "up": ["up", "k"],
    "down": ["down", "j"],
    "page_up": ["pgup"],
    "page_down": ["pgdn"],
    "top": ["home", "g"],
    "bottom": ["end", "G"],
    "select": ["enter"],
    "jump_playing": ["c"],
    "lyrics": ["l"],
    "cover": ["i"],
    "video": ["v"],
    "shuffle": ["s"],
    "repeat": ["r"],
    "volume_up": ["+", "="],
    "volume_down": ["-", "_"],
    "mute": ["m"],
    "speed_up": ["]"],
    "speed_down": ["["],
    "search": ["/"],
    "favorite": ["f"],
    "favorites_only": ["F"],
    "playlists": ["P"],
    "add_to_playlist": ["a"],
    "remove_track": ["delete", "x"],
    "move_up": ["K", "S-up"],
    "move_down": ["J", "S-down"],
    "fetch_lyrics": ["u"],
    "sleep_timer": ["t"],
    "help": ["?"],
    "quit": ["q"],
}


                                                            
class DiscordRPC:
                                                                                            
    def __init__(self, client_id=DISCORD_CLIENT_ID):
        self.client_id = client_id
        self.sock = None
        self.connected = False
        self._lock = threading.Lock()
        threading.Thread(target=self._connect, daemon=True).start()

    def _socket_paths(self):
        uid = os.getuid() if hasattr(os, "getuid") else 1000
        dirs = [
            os.environ.get("XDG_RUNTIME_DIR", ""),
            f"/run/user/{uid}",
            f"/run/user/{uid}/app/com.discordapp.Discord",
            "/tmp",
            tempfile.gettempdir(),
        ]
        paths = []
        for d in dirs:
            if d and os.path.isdir(d):
                for i in range(10):
                    paths.append(os.path.join(d, f"discord-ipc-{i}"))
        return paths

    def _connect(self):
        for path in self._socket_paths():
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.settimeout(1.0)
                s.connect(path)
                payload = json.dumps({"v": 1, "client_id": self.client_id}).encode("utf-8")
                s.sendall(struct.pack("<II", 0, len(payload)) + payload)
                hdr = s.recv(8)
                if len(hdr) == 8:
                    _, resp_len = struct.unpack("<II", hdr)
                    s.recv(resp_len)
                    self.sock = s
                    self.connected = True
                    break
            except Exception:
                continue

    def update(self, track, paused, pos, dur):
        if not self.connected or not self.sock:
            return
        with self._lock:
            try:
                now = int(time.time())
                start_ts = now - int(pos) if not paused else None
                end_ts = (now - int(pos) + int(dur)) if (dur and not paused) else None

                activity = {
                    "details": track.title[:128] if track else "Idle",
                    "state": ((f"{track.artist} • {track.album}" if track.artist else "sxmply music")[:128]) if track else "Paused",
                    "assets": {
                        "large_image": "icon",
                        "large_text": "sxmply music",
                        "small_image": "pause" if paused else "play",
                        "small_text": "Paused" if paused else "Playing",
                    },
                }
                if start_ts:
                    activity["timestamps"] = {"start": start_ts}
                    if end_ts:
                        activity["timestamps"]["end"] = end_ts

                data = json.dumps({
                    "cmd": "SET_ACTIVITY",
                    "args": {"pid": os.getpid(), "activity": activity},
                    "nonce": str(time.time()),
                }).encode("utf-8")

                self.sock.sendall(struct.pack("<II", 1, len(data)) + data)
            except Exception:
                self.connected = False

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass


                                                        
def strip_ansi(text):
    return _ANSI_RE.sub("", str(text))


def _cw(ch):
    if unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def width(text):
    return sum(_cw(c) for c in strip_ansi(text))


def cut(text, w):
    out, used = [], 0
    for ch in text:
        c = _cw(ch)
        if used + c > w:
            break
        out.append(ch)
        used += c
    return "".join(out)


def fit(text, w):
    if w <= 0:
        return ""
    w_vis = width(text)
    if w_vis > w:
        text = cut(text, max(w - 1, 0)) + "…"
        w_vis = width(text)
    return text + " " * max(w - w_vis, 0)


def wrap(text, w):
    w = max(w, 2)
    out, line = [], ""
    for word in text.split():
        cand = f"{line} {word}" if line else word
        if width(cand) <= w:
            line = cand
            continue
        if line:
            out.append(line)
        while width(word) > w:
            piece = cut(word, w)
            if not piece:
                break
            out.append(piece)
            word = word[len(piece):]
        line = word
    if line:
        out.append(line)
    return out or [""]


def has_display():
    return sys.platform == "darwin" or bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


@dataclass
class Layout:
    left_w: int
    panel_w: int
    art_cols: int
    art_rows: int
    art_x: int
    art_y: int


def fmt_time(sec):
    sec = int(max(sec, 0))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


class MusicApp:
    def __init__(self, tracks, shuffle=False, repeat="off", favorites_only=False,
                 roots=None, images="auto"):
        self.all = list(tracks)
        self.view = list(tracks)
        self.roots = list(roots or [])
        self.images = images
        self.cursor = 0
        self.top = 0
        self.filter = ""
        self.searching = False
        self.fav_only = favorites_only

                                                                             
        cfg = config.load("music")
        self.favorites = set(cfg.get("favorites") or [])
        self.playlists = cfg.get("playlists") or {}

                                     
        self.theme = {**DEFAULT_THEME, **(cfg.get("theme") or {})}
        self.keybinds = {**DEFAULT_KEYBINDS, **(cfg.get("keybinds") or {})}

        if "theme" not in cfg or "keybinds" not in cfg:
            cfg["theme"] = self.theme
            cfg["keybinds"] = self.keybinds
            config.save(cfg, "music")

        self.active_playlist = None
        self.mode = "tracks"
        self.pl_items = []
        self.pl_cursor = 0
        self.pl_top = 0

        self.queue = Queue()
        self.queue.shuffle = shuffle
        self.queue.repeat = repeat
        self.playing = None
        self.player = MpvPlayer(volume=cfg.get("volume", 70))
        self.message = ""
        self.message_until = 0.0
        self.sleep_at = None
        self.sleep_idx = 0
        self.show_help = False
        self.errors = 0
        self.direction = 1
        self.quit = False
        self._last_frame = ""

        self.prompt_mode = None
        self.prompt_text = ""
        self.prompt_target = None

        self.show_art = True
        self.show_lyrics = False
        self.want_video = False
        self.lyr_follow, self.lyr_top, self._lyr_total, self._lyr_h = True, 0, 0, 1
        self._lyr_cache = {}
        self.confirm = None
        self.reader = None
        self.art_mode = "off" if images == "off" else "ansi"
        self.cell = (10, 20)
        self.true_color = art.truecolor()
        self.loader = art.ArtLoader()
        self._art_sig = None
        self._size = None

                              
        self.discord = DiscordRPC() if cfg.get("discord_rpc", True) else None

        self.refresh_view()

                                                   
    def c(self, role):
        return self.theme.get(role, DEFAULT_THEME.get(role, "gray"))

    def is_key(self, k, action):
        bindings = self.keybinds.get(action, [])
        if isinstance(bindings, str):
            bindings = [bindings]
                                                    
        if k == " ":
            return " " in bindings or "space" in bindings
        return k in bindings

    def key_hint(self, action):
        b = self.keybinds.get(action, DEFAULT_KEYBINDS.get(action, []))
        return "/".join(b) if isinstance(b, list) else str(b)

    def say(self, text, seconds=2.5):
        self.message, self.message_until = text, time.monotonic() + seconds

    def selected(self):
        view = getattr(self, "view", None)
        return view[self.cursor] if view and 0 <= self.cursor < len(view) else None

    def save_music_config(self):
        cfg = config.load("music")
        cfg["favorites"] = sorted(self.favorites)
        cfg["playlists"] = self.playlists
        cfg["volume"] = self.player.volume
        config.save(cfg, "music")

                                                
    def visualizer_bar(self, width=12):
        if not self.playing:
            return " " * width
        if self.player.paused:
            return "·" * width
        chars = [" ", " ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
        t = time.monotonic() * 8
        out = []
        for i in range(width):
            val = (math.sin(t + i * 0.8) * 0.4 + math.sin(t * 1.5 + i * 1.4) * 0.35 + math.sin(t * 0.6 - i * 0.5) * 0.25)
            lvl = int(max(0, min(1, (val + 1) / 2)) * (len(chars) - 1))
            out.append(chars[lvl])
        return "".join(out)

    def refresh_view(self, reset_cursor=False):
        keep = self.selected()
        words = self.filter.lower().split()

        if self.active_playlist and self.active_playlist in self.playlists:
            allowed = set(self.playlists[self.active_playlist])
            base_list = [t for t in self.all if t.path in allowed]
        elif self.fav_only:
            base_list = [t for t in self.all if t.path in self.favorites]
        else:
            base_list = self.all

        self.view = [t for t in base_list if all(w in t.haystack for w in words)]
        if reset_cursor:
            self.cursor = 0
        elif keep in self.view:
            self.cursor = self.view.index(keep)
        else:
            self.cursor = min(self.cursor, max(len(self.view) - 1, 0))

    def refresh_playlists_view(self):
        items = [
            {"kind": "all", "name": "★ All Tracks", "count": len(self.all), "desc": "Full library"},
            {"kind": "fav", "name": "♥ Favorites", "count": len(self.favorites), "desc": "Hearted songs"},
        ]
        for name in sorted(self.playlists.keys()):
            count = len(self.playlists[name])
            items.append({"kind": "custom", "name": f"♪ {name}", "raw_name": name, "count": count, "desc": "Custom playlist"})
        items.append({"kind": "new", "name": "[+] Create New Playlist", "count": 0, "desc": "Press enter or 'n'"})
        self.pl_items = items
        self.pl_cursor = min(self.pl_cursor, max(len(items) - 1, 0))

                                    
    def start_playing(self, index=0):
        if not self.view:
            return
        self.direction = 1
        self.queue.set_tracks(self.view, index)
        self.play(self.queue.current)

    def play(self, track):
        self.playing = track
        self.lyr_follow, self.lyr_top = True, 0
        if track:
            self.player.load(track.path)
        else:
            self.player.stop()
        if self.discord:
            self.discord.update(track, self.player.paused, self.player.position, self.player.duration)

    def next_track(self, auto=False):
        self.direction = 1
        track = self.queue.advance(auto=auto)
        if track is None and auto:
            self.say("End of queue. Press enter to replay.", 5)
        self.play(track)

    def previous_track(self):
        if self.player.position > 3:
            self.player.seek(0, "absolute")
        else:
            self.direction = -1
            self.play(self.queue.previous())

    def drain_events(self):
        while not self.player.events.empty():
            ev = self.player.events.get_nowait()
            if ev[0] == "loaded":
                self.errors = 0
                want = self.want_video and bool(self.playing and self.playing.is_video)
                if want != self.player.video_on:
                    self.player.set_video(want)
                if self.discord:
                    self.discord.update(self.playing, self.player.paused, self.player.position, self.player.duration)
            elif ev[0] == "end":
                if ev[1] == "error":
                    self.errors += 1
                    if self.playing:
                        self.say(f"Can't play {self.playing.title}", 4)
                    if self.errors >= max(len(self.queue.tracks), 1):
                        self.say("None of these files can be played.", 6)
                        self.play(None)
                        continue
                if ev[1] == "error" and self.direction < 0:
                    self.play(self.queue.previous())
                else:
                    self.next_track(auto=True)
            elif ev[0] == "closed" and not self.quit:
                self.say("mpv stopped unexpectedly. Press q and start again.", 10)

    def check_sleep(self):
        if self.sleep_at and time.monotonic() >= self.sleep_at:
            self.sleep_at, self.sleep_idx = None, 0
            self.player.pause()
            self.say("Sleep timer finished: paused. Good night.", 10)

                                                    
    def fetch_lyrics_for(self, track):
        if not track:
            return
        self.say(f"Searching lyrics for '{track.title}'…", 6)
        threading.Thread(target=self._fetch_lyrics_worker, args=(track,), daemon=True).start()

    def _fetch_lyrics_worker(self, track):
        try:
            from ..clip import metadata
            tags = metadata.Tags(title=track.title, artist=track.artist, album=track.album, duration=track.duration)
            text, synced = metadata.fetch_lyrics(tags)
            if text:
                metadata._write_sidecar(track.path, text, synced)
                self._lyr_cache[track.path] = lyrics.load(track.path)
                self.say(f"✔ Lyrics saved for '{track.title}'", 4)
            else:
                self.say(f"No lyrics found on LRCLIB for '{track.title}'", 4)
        except Exception as e:
            self.say(f"Lyrics lookup error ({e})", 4)

                                        
    def handle_key(self, k):
        if self.confirm:
            kind, query = self.confirm
            self.confirm = None
            if k in ("y", "Y"):
                self.download_via_clip(query)
            else:
                self.say("OK. Esc clears the search.")
            return

        if self.prompt_mode:
            self.handle_prompt_key(k)
            return

        if self.show_help:
            self.show_help = False
            return

        if self.searching:
            self.search_key(k)
            return

        if self.mode == "playlists":
            self.handle_playlists_key(k)
            return

        p = self.player
        if self.is_key(k, "play_pause"):
            if self.playing:
                p.toggle_pause()
                if self.discord:
                    self.discord.update(self.playing, p.paused, p.position, p.duration)
            else:
                self.start_playing(self.cursor)
        elif self.is_key(k, "next"):
            self.next_track()
        elif self.is_key(k, "prev"):
            self.previous_track()
        elif self.is_key(k, "seek_forward"):
            p.seek(SEEK_SMALL)
        elif self.is_key(k, "seek_backward"):
            p.seek(-SEEK_SMALL)
        elif self.is_key(k, "seek_forward_large"):
            p.seek(SEEK_BIG)
        elif self.is_key(k, "seek_backward_large"):
            p.seek(-SEEK_BIG)
        elif self.is_key(k, "down"):
            self.move(1)
        elif self.is_key(k, "up"):
            self.move(-1)
        elif self.is_key(k, "page_down"):
            self.move(self.page_size())
        elif self.is_key(k, "page_up"):
            self.move(-self.page_size())
        elif self.is_key(k, "top"):
            self.cursor = 0
        elif self.is_key(k, "bottom"):
            self.cursor = max(len(self.view) - 1, 0)
        elif self.is_key(k, "select"):
            if self.view:
                self.start_playing(self.cursor)
        elif self.is_key(k, "jump_playing"):
            if self.show_lyrics:
                self.lyr_follow = True
            elif self.playing in self.view:
                self.cursor = self.view.index(self.playing)
        elif self.is_key(k, "lyrics"):
            self.show_lyrics = not self.show_lyrics
            self.lyr_follow = True
        elif self.is_key(k, "fetch_lyrics"):
            t = self.selected() or self.playing
            if t:
                self.fetch_lyrics_for(t)
        elif self.is_key(k, "move_up"):
            self.reorder_playlist_song(-1)
        elif self.is_key(k, "move_down"):
            self.reorder_playlist_song(1)
        elif self.is_key(k, "cover"):
            self.show_art = not self.show_art
            self.say("Cover panel shown" if self.show_art else "Cover panel hidden")
        elif self.is_key(k, "video"):
            self.toggle_video()
        elif self.is_key(k, "shuffle"):
            self.queue.set_shuffle(not self.queue.shuffle)
            self.say("Shuffle on" if self.queue.shuffle else "Shuffle off")
        elif self.is_key(k, "repeat"):
            self.say({"off": "Repeat off", "all": "Repeat all", "one": "Repeat this song"}[self.queue.cycle_repeat()])
        elif self.is_key(k, "volume_up"):
            p.set_volume(p.volume + 5)
        elif self.is_key(k, "volume_down"):
            p.set_volume(p.volume - 5)
        elif self.is_key(k, "mute"):
            p.toggle_mute()
        elif self.is_key(k, "speed_up"):
            p.set_speed(p.speed + 0.25)
        elif self.is_key(k, "speed_down"):
            p.set_speed(p.speed - 0.25)
        elif self.is_key(k, "search"):
            self.searching = True
        elif self.is_key(k, "favorite"):
            self.toggle_favorite()
        elif self.is_key(k, "favorites_only"):
            self.fav_only = not self.fav_only
            self.active_playlist = None
            self.refresh_view(reset_cursor=True)
            self.say("Showing favorites" if self.fav_only else "Showing all tracks")
        elif self.is_key(k, "playlists"):
            self.mode = "playlists"
            self.show_lyrics = False
            self.refresh_playlists_view()
        elif self.is_key(k, "add_to_playlist"):
            t = self.selected()
            if t:
                self.prompt_mode = "add_to_playlist"
                self.prompt_target = t
                self.prompt_text = ""
        elif self.is_key(k, "remove_track"):
            t = self.selected()
            if t and self.active_playlist and self.active_playlist in self.playlists:
                pl = self.playlists[self.active_playlist]
                if t.path in pl:
                    pl.remove(t.path)
                    self.save_music_config()
                    self.refresh_view()
                    self.say(f"Removed '{t.title}' from '{self.active_playlist}'")
        elif self.is_key(k, "sleep_timer"):
            self.cycle_sleep()
        elif self.is_key(k, "help"):
            self.show_help = True
        elif k == "esc":
            if self.show_lyrics:
                self.show_lyrics = False
            elif self.filter:
                self.filter = ""
                self.refresh_view()
            elif self.active_playlist or self.fav_only:
                self.active_playlist = None
                self.fav_only = False
                self.refresh_view(reset_cursor=True)
                self.say("Showing all tracks")
            else:
                self.quit = True
        elif self.is_key(k, "quit"):
            self.quit = True

    def reorder_playlist_song(self, direction):
        if not (self.active_playlist and self.active_playlist in self.playlists):
            self.say("Open a custom playlist with 'P' to reorder tracks.")
            return
        t = self.selected()
        if not t:
            return
        pl = self.playlists[self.active_playlist]
        if t.path not in pl:
            return
        pos = pl.index(t.path)
        new_pos = pos + direction
        if 0 <= new_pos < len(pl):
            pl[pos], pl[new_pos] = pl[new_pos], pl[pos]
            self.save_music_config()
            self.refresh_view()
            self.cursor = max(0, min(len(self.view) - 1, self.cursor + direction))

    def handle_playlists_key(self, k):
        if self.is_key(k, "up"):
            self.pl_cursor = max(0, self.pl_cursor - 1)
        elif self.is_key(k, "down"):
            self.pl_cursor = min(len(self.pl_items) - 1, self.pl_cursor + 1)
        elif self.is_key(k, "top"):
            self.pl_cursor = 0
        elif self.is_key(k, "bottom"):
            self.pl_cursor = max(0, len(self.pl_items) - 1)
        elif self.is_key(k, "select"):
            self.select_playlist_item(self.pl_cursor)
        elif k in ("n", "c", "+"):
            self.prompt_mode = "new_playlist"
            self.prompt_text = ""
        elif self.is_key(k, "remove_track") or k == "d":
            if 0 <= self.pl_cursor < len(self.pl_items):
                item = self.pl_items[self.pl_cursor]
                if item["kind"] == "custom":
                    self.prompt_mode = "delete_playlist"
                    self.prompt_target = item["raw_name"]
                else:
                    self.say("Cannot delete system playlists.")
        elif k == "r":
            if 0 <= self.pl_cursor < len(self.pl_items):
                item = self.pl_items[self.pl_cursor]
                if item["kind"] == "custom":
                    self.prompt_mode = "rename_playlist"
                    self.prompt_target = item["raw_name"]
                    self.prompt_text = item["raw_name"]
                else:
                    self.say("Cannot rename system playlists.")
        elif self.is_key(k, "playlists") or k == "esc":
            self.mode = "tracks"
            self.refresh_view()
        elif self.is_key(k, "help"):
            self.show_help = True
        elif self.is_key(k, "quit"):
            self.quit = True

    def select_playlist_item(self, idx):
        if not (0 <= idx < len(self.pl_items)):
            return
        item = self.pl_items[idx]
        kind = item["kind"]
        if kind == "all":
            self.active_playlist = None
            self.fav_only = False
            self.mode = "tracks"
            self.refresh_view(reset_cursor=True)
            self.say("All tracks")
        elif kind == "fav":
            self.active_playlist = None
            self.fav_only = True
            self.mode = "tracks"
            self.refresh_view(reset_cursor=True)
            self.say("Favorites (♥)")
        elif kind == "custom":
            self.active_playlist = item["raw_name"]
            self.fav_only = False
            self.mode = "tracks"
            self.refresh_view(reset_cursor=True)
            self.say(f"Playlist: {item['raw_name']}")
        elif kind == "new":
            self.prompt_mode = "new_playlist"
            self.prompt_text = ""

    def handle_prompt_key(self, k):
        if k == "esc":
            self.prompt_mode = None
            self.prompt_text = ""
            self.prompt_target = None
            self.say("Canceled.")
            return

        if self.prompt_mode == "delete_playlist":
            if k in ("y", "Y"):
                target = self.prompt_target
                if target in self.playlists:
                    del self.playlists[target]
                    self.save_music_config()
                    if self.active_playlist == target:
                        self.active_playlist = None
                        self.refresh_view(reset_cursor=True)
                    self.say(f"Deleted playlist '{target}'")
                    self.refresh_playlists_view()
            else:
                self.say("Canceled.")
            self.prompt_mode = None
            self.prompt_target = None
            return

        if k == "backspace":
            self.prompt_text = self.prompt_text[:-1]
        elif k == "enter":
            entered = self.prompt_text.strip()
            if self.prompt_mode == "new_playlist":
                if entered:
                    if entered not in self.playlists:
                        self.playlists[entered] = []
                        self.save_music_config()
                        self.say(f"✔ Created playlist '{entered}'")
                        if self.mode == "playlists":
                            self.refresh_playlists_view()
                    else:
                        self.say(f"Playlist '{entered}' already exists.")
            elif self.prompt_mode == "rename_playlist":
                old_name = self.prompt_target
                if entered and entered != old_name:
                    self.playlists[entered] = self.playlists.pop(old_name, [])
                    if self.active_playlist == old_name:
                        self.active_playlist = entered
                    self.save_music_config()
                    self.say(f"✔ Renamed to '{entered}'")
                    if self.mode == "playlists":
                        self.refresh_playlists_view()
            elif self.prompt_mode == "add_to_playlist":
                track = self.prompt_target
                names = sorted(self.playlists.keys())
                target_name = None
                if entered.isdigit() and 1 <= int(entered) <= len(names):
                    target_name = names[int(entered) - 1]
                elif entered:
                    target_name = entered

                if target_name:
                    pl = self.playlists.setdefault(target_name, [])
                    if track.path in pl:
                        pl.remove(track.path)
                        self.say(f"Removed '{track.title}' from '{target_name}'")
                    else:
                        pl.append(track.path)
                        self.say(f"✔ Added to '{target_name}'")
                    self.save_music_config()
                    if self.active_playlist == target_name:
                        self.refresh_view()

            self.prompt_mode = None
            self.prompt_text = ""
            self.prompt_target = None
        elif len(k) == 1 and k.isprintable():
            self.prompt_text += k

    def search_key(self, k):
        if k == "enter":
            self.searching = False
            words = self.filter.lower().split()
            nothing = bool(words) and not any(all(w in t.haystack for w in words) for t in self.all)
            if nothing:
                self.confirm = ("download", self.filter.strip())
        elif k == "esc":
            self.searching, self.filter = False, ""
            self.refresh_view()
        elif k == "backspace":
            self.filter = self.filter[:-1]
            self.refresh_view(reset_cursor=True)
        elif self.is_key(k, "down"):
            self.move(1)
        elif self.is_key(k, "up"):
            self.move(-1)
        elif len(k) == 1 and k.isprintable():
            self.filter += k
            self.refresh_view(reset_cursor=True)

    def move(self, delta):
        if self.show_lyrics:
            self.lyr_follow = False
            self.lyr_top = max(0, min(self.lyr_top + delta, max(self._lyr_total - self._lyr_h, 0)))
        elif self.mode == "playlists":
            self.pl_cursor = max(0, min(len(self.pl_items) - 1, self.pl_cursor + delta))
        elif self.view:
            self.cursor = max(0, min(len(self.view) - 1, self.cursor + delta))

    def page_size(self):
        return max(shutil.get_terminal_size((80, 24)).lines - 8, 1)

    def toggle_video(self):
        t = self.playing
        if not t or not t.is_video:
            self.say("This song has no video.")
        elif not has_display():
            self.say("No graphical display found for a video window.", 5)
        else:
            self.want_video = not self.want_video
            self.player.set_video(self.want_video)
            self.say("Video window opened." if self.want_video else "Video window closed.")

    def lyrics_for(self, track):
        if track.path not in self._lyr_cache:
            try:
                self._lyr_cache[track.path] = lyrics.load(track.path)
            except Exception:
                self._lyr_cache[track.path] = None
        return self._lyr_cache[track.path]

    def download_dir(self):
        for r in self.roots:
            p = os.path.abspath(os.path.expanduser(r))
            if os.path.isdir(p):
                return p
        return os.path.abspath(os.path.expanduser(
            config.get("music_dir", tool="music") or config.default_dir("music")))

    def download_via_clip(self, query):
        try:
            from ..clip import cli as clip_cli
        except ImportError as e:
            self.say(f"sxmply clip isn't available ({e}). Run ./install.sh.", 8)
            return
        dest = self.download_dir()
        before = {t.path for t in self.all}
        started = time.time() - 2

        self.leave_screen()
        try:
            print()
            ui.info(f"Searching for “{query}”. Downloads go to {dest}")
            try:
                clip_cli.main(["-D", dest, "--", "search", *query.split()])
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print()
                ui.warn("Canceled.")
            except Exception as e:
                ui.error(f"Download failed: {e}")
            try:
                ui.ask("Press Enter to go back to the player")
            except (EOFError, KeyboardInterrupt):
                print()
        finally:
            self.enter_screen()

        new = []
        try:
            new = [t for t in library.find_tracks([dest], recursive=False)
                   if t.path not in before and os.path.getmtime(t.path) >= started]
        except OSError:
            pass
        if not new:
            self.say("Nothing new was downloaded.")
            return
        for t in new:
            library.read_tags(t)
        self.all.extend(new)
        if self.active_playlist and self.active_playlist in self.playlists:
            for t in new:
                self.playlists[self.active_playlist].append(t.path)
            self.save_music_config()

        self.filter = ""
        self.refresh_view(reset_cursor=True)
        if new[0] in self.view:
            self.cursor = self.view.index(new[0])
            self.start_playing(self.cursor)
        self.say(f"Added {len(new)} song(s) to library", 5)

    def leave_screen(self):
        sys.stdout.write(art.KITTY_DELETE + LEAVE_SCREEN)
        sys.stdout.flush()
        if self.reader:
            self.reader.suspend()

    def enter_screen(self):
        if self.reader:
            self.reader.resume()
        sys.stdout.write(ENTER_SCREEN)
        sys.stdout.flush()
        self._last_frame, self._art_sig, self._size = "", None, None

    def toggle_favorite(self):
        t = self.selected()
        if not t:
            return
        if t.path in self.favorites:
            self.favorites.discard(t.path)
            self.say(f"Removed from favorites: {t.title}")
        else:
            self.favorites.add(t.path)
            self.say(f"♥ Added to favorites: {t.title}")
        self.save_music_config()
        if self.fav_only:
            self.refresh_view()

    def cycle_sleep(self):
        self.sleep_idx = (self.sleep_idx + 1) % len(SLEEP_CHOICES)
        minutes = SLEEP_CHOICES[self.sleep_idx]
        if minutes:
            self.sleep_at = time.monotonic() + minutes * 60
            self.say(f"Sleep timer: {minutes} minutes")
        else:
            self.sleep_at = None
            self.say("Sleep timer off")

                                   
    def header(self, w):
        left_plain = "♪ sxmply music"
        chips = []
        if self.mode == "playlists":
            chips.append("playlists browser")
        elif self.active_playlist:
            chips.append(f"playlist: {self.active_playlist}")
        elif self.fav_only:
            chips.append("♥ favorites")
        if self.queue.shuffle:
            chips.append("shuffle")
        if self.queue.repeat != "off":
            chips.append(f"repeat {self.queue.repeat}")
        if self.show_lyrics:
            chips.append("lyrics")
        if self.sleep_at:
            chips.append(f"sleep {max(int((self.sleep_at - time.monotonic()) / 60) + 1, 1)}m")
        count = f"{len(self.view)}/{len(self.all)}" if len(self.view) != len(self.all) else str(len(self.all))
        chips.append(f"{count} tracks")
        right = cut("  ·  ".join(chips), max(w - width(left_plain) - 2, 0))
        gap = " " * max(w - width(left_plain) - width(right), 1)
        return ui.paint(left_plain, self.c("primary"), "bold") + gap + ui.paint(right, self.c("accent"))

    def help_card(self, w, h):
        c_pp = self.key_hint("play_pause")
        c_nxt = f"{self.key_hint('next')} / {self.key_hint('prev')}"
        c_sk = f"{self.key_hint('seek_backward')} / {self.key_hint('seek_forward')}"
        c_pl = self.key_hint("playlists")
        c_add = self.key_hint("add_to_playlist")
        c_fav = f"{self.key_hint('favorite')} / {self.key_hint('favorites_only')}"
        c_rem = self.key_hint("remove_track")
        c_reorder = f"{self.key_hint('move_up')} / {self.key_hint('move_down')}"
        c_lyr = f"{self.key_hint('lyrics')} / {self.key_hint('fetch_lyrics')} (fetch)"
        c_vol = f"{self.key_hint('volume_down')} / {self.key_hint('volume_up')} / {self.key_hint('mute')}"
        c_srch = self.key_hint("search")

        card = [
            "┌── Shortcuts & Controls (Customizable in config.json) ────────────────┐",
            "│ [Playback]                                                           │",
            f"│   {fit(c_pp, 14)} Play / Pause          {fit(c_nxt, 14)} Next / Prev    │",
            f"│   {fit(c_sk, 14)} Seek 5s (Shift: 30s)  s / r          Shuffle/Repeat │",
            "│                                                                      │",
            "│ [Playlists & Favs]                                                   │",
            f"│   {fit(c_pl, 14)} Playlists browser     {fit(c_add, 14)} Add to playlist│",
            f"│   {fit(c_fav, 14)} Favorite / Favs view  {fit(c_rem, 14)} Remove track   │",
            f"│   {fit(c_reorder, 14)} Move song up/down                                   │",
            "│                                                                      │",
            "│ [Lyrics & Visuals]                                                   │",
            f"│   {fit(c_lyr, 14)} Show / Fetch online   i / v          Cover / Video  │",
            "│                                                                      │",
            "│ [Sound & Navigation]                                                 │",
            f"│   {fit(c_vol, 14)} Volume / Mute         [ / ]          Speed (0.5-2x) │",
            f"│   {fit(c_srch, 14)} Search (Enter: fetch) c              Jump to track  │",
            "│   ↑ / ↓ (k / j)  Browse tracks         ? / esc        Close / Back   │",
            "└──────────────────────────────────────────────────────────────────────┘",
        ]
        out = [fit("", w)]
        for line in card:
            out.append(fit(f"  {line}", w))
        while len(out) < h:
            out.append(fit("", w))
        return out[:h]

    def list_lines(self, w, h):
        if self.show_help:
            return self.help_card(w, h)

        if self.mode == "playlists":
            return self.playlists_lines(w, h)

        if not self.view:
            msg = "No songs match." if (self.filter or self.fav_only or self.active_playlist) else "No songs."
            return [fit("  " + msg, w)] + [fit("", w)] * (h - 1)

        content_h = max(h - 2, 1)
        if self.cursor < self.top:
            self.top = self.cursor
        elif self.cursor >= self.top + content_h:
            self.top = self.cursor - content_h + 1
        self.top = max(0, min(self.top, max(len(self.view) - content_h, 0)))

                                          
        num_w = max(len(str(len(self.view))), 2) + 4
        dur_w = 6
        fav_w = 2
        year_w = 6 if w >= 80 else 0
        album_w = int((w - num_w - dur_w - fav_w - year_w - 6) * 0.28) if w >= 110 else 0
        artist_w = int((w - num_w - dur_w - fav_w - year_w - album_w - 6) * 0.35) if w >= 70 else 0
        title_w = max(w - num_w - dur_w - fav_w - year_w - album_w - artist_w - 6, 12)

        hdr_num = fit("  #", num_w)
        hdr_title = fit("TITLE", title_w)
        hdr_artist = (" " + fit("ARTIST", artist_w)) if artist_w else ""
        hdr_album = (" " + fit("ALBUM", album_w)) if album_w else ""
        hdr_year = (" " + fit("YEAR", year_w)) if year_w else ""
        hdr_dur = " " + fit("TIME", dur_w)
        hdr_fav = "  "
        header_line = ui.paint(fit(hdr_num + hdr_title + hdr_artist + hdr_album + hdr_year + hdr_dur + hdr_fav, w), "bold", self.c("dim"))

        rows = [header_line]
        for i in range(self.top, min(self.top + content_h, len(self.view))):
            t = self.view[i]
            is_cur, is_play = i == self.cursor, t is self.playing
            mark = "▶" if is_play and not self.player.paused else "‖" if is_play else " "
            cur_marker = "›" if is_cur else " "

            col_num = fit(f"{cur_marker}{mark} {i + 1}", num_w)
            col_title = fit(t.title, title_w)
            col_artist = (" " + fit(t.artist or "—", artist_w)) if artist_w else ""
            col_album = (" " + fit(t.album or "—", album_w)) if album_w else ""
            col_year = (" " + fit(t.year or "—", year_w)) if year_w else ""
            col_dur = " " + fit(fmt_time(t.duration) if t.duration else "", dur_w)
            col_fav = " ♥" if t.path in self.favorites else "  "

            raw_line = col_num + col_title + col_artist + col_album + col_year + col_dur + col_fav
            line_text = fit(raw_line, w)

            if is_cur:
                rows.append(ui.paint(line_text, self.c("cursor")))
            elif is_play:
                rows.append(ui.paint(line_text, self.c("playing"), "bold"))
            elif t.path in self.favorites:
                idx = line_text.rfind("♥")
                if idx != -1:
                    rows.append(line_text[:idx] + ui.paint("♥", self.c("heart")) + line_text[idx + 1:])
                else:
                    rows.append(line_text)
            else:
                rows.append(line_text)

        while len(rows) < h:
            rows.append(fit("", w))
        return rows[:h]

    def playlists_lines(self, w, h):
        content_h = max(h - 2, 1)
        if self.pl_cursor < self.pl_top:
            self.pl_top = self.pl_cursor
        elif self.pl_cursor >= self.pl_top + content_h:
            self.pl_top = self.pl_cursor - content_h + 1
        self.pl_top = max(0, min(self.pl_top, max(len(self.pl_items) - content_h, 0)))

        name_w = max(int(w * 0.45), 20)
        count_w = 14
        desc_w = max(w - name_w - count_w - 6, 10)

        header_line = ui.paint(fit("  PLAYLIST" + " " * (name_w - 8) + fit("TRACKS", count_w) + fit("DESCRIPTION", desc_w), w), "bold", self.c("dim"))
        rows = [header_line]

        for i in range(self.pl_top, min(self.pl_top + content_h, len(self.pl_items))):
            it = self.pl_items[i]
            is_cur = i == self.pl_cursor
            cur_marker = "› " if is_cur else "  "
            cnt_str = f"{it['count']} tracks" if it['kind'] != "new" else ""
            line_text = fit(cur_marker + fit(it['name'], name_w) + fit(cnt_str, count_w) + fit(it['desc'], desc_w), w)
            if is_cur:
                rows.append(ui.paint(line_text, self.c("cursor")))
            elif it['kind'] == "new":
                rows.append(ui.paint(line_text, self.c("accent")))
            else:
                rows.append(line_text)

        while len(rows) < h:
            rows.append(fit("", w))
        return rows[:h]

    def now_playing(self, w):
        t, p = self.playing, self.player
        if t is None:
            return [ui.paint(fit("  Nothing playing. Press enter on a song.", w), self.c("dim")),
                    fit("", w), self.progress(w, 0, 0)]
        if p.duration and not t.duration:
            t.duration = p.duration
        state = "‖ Paused" if p.paused else "▶ Playing"
        l1 = ui.paint(fit(f"{state}  {t.title}", w), "bold")
        info = " · ".join(x for x in (t.artist, t.album) if x) or os.path.basename(os.path.dirname(t.path))
        l2 = ui.paint(fit("  " + info, w), self.c("dim"))
        return [l1, l2, self.progress(w, p.position, p.duration or t.duration)]

    def progress(self, w, pos, dur):
        p = self.player
        pos = min(pos, dur) if dur else pos
        times = f"{fmt_time(pos)} / {fmt_time(dur)}" if dur else fmt_time(pos)
        right = "muted" if p.muted else f"vol {p.volume}%"
        if p.speed != 1:
            right += f"  {p.speed:g}x"

                             
        viz_bars = f"  [{self.visualizer_bar(8)}]" if w >= 60 else ""

        bar_w = w - width(times) - width(right) - width(viz_bars) - 4
        if bar_w < 8:
            viz_bars = ""
            bar_w = w - width(times) - width(right) - 4
        if bar_w < 8:
            right, bar_w = "", w - width(times) - 2

        bar_w = max(bar_w, 1)
        filled = int(bar_w * (pos / dur)) if dur else 0
        bar = ui.paint(BAR_CHAR * filled, self.c("playing")) + ui.paint(EMPTY_CHAR * (bar_w - filled), self.c("dim"))
        viz_painted = ui.paint(viz_bars, self.c("playing")) if viz_bars else ""
        return f"{bar} {times}  {ui.paint(right, self.c('accent'))}{viz_painted}"

    def footer(self, w):
        if self.confirm:
            return ui.paint(fit(" Song not found. Download via sxmply clip? (y/N)", w), self.c("highlight"), "bold")

        if self.prompt_mode == "delete_playlist":
            return ui.paint(fit(f" Delete playlist '{self.prompt_target}'? (y/N)", w), "red", "bold")

        if self.prompt_mode == "new_playlist":
            return ui.paint(fit(f" New playlist name: {self.prompt_text}█    enter: save   esc: cancel", w), self.c("highlight"), "bold")

        if self.prompt_mode == "rename_playlist":
            return ui.paint(fit(f" Rename '{self.prompt_target}' to: {self.prompt_text}█    enter: save   esc: cancel", w), self.c("highlight"), "bold")

        if self.prompt_mode == "add_to_playlist":
            names = sorted(self.playlists.keys())
            opts = " ".join(f"[{i+1}]{n}" for i, n in enumerate(names[:4]))
            hint = f"Add to playlist ({opts or 'type new name'}): "
            return ui.paint(fit(f" {hint}{self.prompt_text}█    enter: save   esc: cancel", w), self.c("highlight"), "bold")

        if self.searching:
            return ui.paint(fit(f"/ {self.filter}█    enter: keep   esc: clear", w), self.c("highlight"))

        if self.message and time.monotonic() < self.message_until:
            return ui.paint(fit(" " + self.message, w), self.c("highlight"))

        if self.mode == "playlists":
            hint = "enter select · n new · d delete · r rename · P/esc back · ? help · q quit"
        else:
            hint = f"space pause · n/b next/prev · {self.key_hint('playlists')} playlists · {self.key_hint('add_to_playlist')} add · {self.key_hint('move_up')}/{self.key_hint('move_down')} reorder · u lyrics · ? help"
        return ui.paint(fit(" " + hint, w), self.c("dim"))

                                       
    def lyrics_lines(self, w, h):
        t = self.playing
        ly = self.lyrics_for(t) if t else None
        kind = "" if ly is None else "  ·  synced" if ly.synced else "  ·  not synced"
        head = ui.paint(fit("  ♪ Lyrics" + kind + (f"  ·  {t.title}" if t else ""), w), "bold")
        blank = fit("", w)
        self._lyr_h = max(h - 2, 1)
        if t is None or ly is None:
            msg = (["  Nothing is playing."] if t is None else
                   ["  No lyrics for this song.", "",
                    "  Press 'u' to search and download lyrics from LRCLIB.",
                    "  You can also put a .lrc file in the hidden .lyrics/ folder."])
            self._lyr_total = 0
            lines = [head, blank] + [ui.paint(fit(m, w), self.c("dim")) for m in msg]
            return (lines + [blank] * h)[:h]

        rows = []
        for n, (t_sec, text) in enumerate(ly.lines):
            shown = text.strip() or ("♪" if ly.synced else "")
            wrap_w = max(w - 12, 10) if ly.synced else max(w - 6, 10)
            for k, part in enumerate(wrap(shown, wrap_w) if shown else [""]):
                rows.append((n, part, k == 0, t_sec))
        self._lyr_total = len(rows)

        cur = ly.index_at(self.player.position) if ly.synced else -1

        if ly.synced and self.lyr_follow:
            target_idx = cur if cur >= 0 else 0
            first = next((i for i, (n, _, _, _) in enumerate(rows) if n == target_idx), 0)
            self.lyr_top = first - self._lyr_h // 2
        self.lyr_top = max(0, min(self.lyr_top, max(len(rows) - self._lyr_h, 0)))

        out = [head, blank]
        for n, text, first, t_sec in rows[self.lyr_top:self.lyr_top + self._lyr_h]:
            if not ly.synced:
                line = fit("    " + text, w)
                out.append(line)
            else:
                time_str = f"{fmt_time(t_sec):>4} " if (first and t_sec is not None) else "     "
                if n == cur:
                    marker = " ▶ " if first else "   "
                    row = fit(f" {time_str}{marker}{text}", w)
                    out.append(ui.paint(row, self.c("playing"), "bold"))
                elif cur == -1 and n == 0 and first:
                    row = fit(f" {time_str} › {text}", w)
                    out.append(ui.paint(row, self.c("accent")))
                elif n < cur:
                    marker = "   "
                    row = fit(f" {time_str}{marker}{text}", w)
                    out.append(ui.paint(row, self.c("dim")))
                else:
                    marker = "   "
                    ts = ui.paint(f" {time_str}", self.c("dim"))
                    words = fit(f"{marker}{text}", max(w - 6, 0))
                    out.append(ts + words)
        return (out + [blank] * h)[:h]

                                       
    def layout(self, w, body_h):
        if not self.show_art or w < 70 or body_h < 8:
            return None
        cw, ch = self.cell
        ratio = ch / cw if cw else 2.0
        art_rows = max(min(body_h - 7, 16), 0)
        if art_rows < 4 or self.art_mode == "off":
            art_rows = 0
        art_cols = int(round(art_rows * ratio))
        if art_cols > 48:
            art_rows = int(48 / ratio)
            art_cols = int(round(art_rows * ratio))
        panel_w = max(art_cols, 28)
        left_w = w - panel_w - 2
        if left_w < 38:
            return None
        lead = (panel_w - art_cols) // 2
        return Layout(left_w, panel_w, art_cols, art_rows, left_w + 3 + lead, 3)

    def info_lines(self, pw):
        t = self.playing
        if t is None:
            return [ui.paint(fit("Nothing playing", pw), self.c("dim"))]
        out = [ui.paint(fit(t.title, pw), "bold")]
        if t.artist:
            out.append(fit(t.artist, pw))
        album = " · ".join(x for x in (t.album, t.year) if x)
        if album:
            out.append(ui.paint(fit(album, pw), self.c("dim")))
        ext = os.path.splitext(t.path)[1].lstrip(".").upper()
        dur = self.player.duration or t.duration
        out.append(ui.paint(fit(" · ".join(x for x in (ext, fmt_time(dur) if dur else "") if x), pw), self.c("dim")))
        ly = self.lyrics_for(t)
        out.append(ui.paint(fit("lyrics: " + ("none" if ly is None else "synced" if ly.synced else "plain")
                                + ("" if ly is None else "  (l)"), pw), self.c("accent") if ly else self.c("dim")))
        if t.is_video:
            out.append(ui.paint(fit("video window on (v)" if self.player.video_on
                                    else "video  (v: show window)", pw), self.c("accent")))
        if t.path in self.favorites:
            out.append(ui.paint(fit("♥ favorite", pw), self.c("heart")))

                                        
        out.append(ui.paint(fit("─" * max(pw - 2, 2), pw), self.c("dim")))
        out.append(ui.paint(fit(self.visualizer_bar(max(pw - 4, 4)), pw), self.c("accent")))

        return out

    def build_frame(self, cols, rows):
        w = max(cols - 1, 20)
        body_h = max(rows - 7, 1)
        lay = self.layout(w, body_h)
        left_w = lay.left_w if lay else w

        if self.show_lyrics and not self.show_help:
            left = self.lyrics_lines(left_w, body_h)
        else:
            left = self.list_lines(left_w, body_h)

        rendered = None
        if lay and lay.art_rows and self.playing:
            spec = art.Spec(self.art_mode, lay.art_cols, lay.art_rows, *self.cell, self.true_color)
            rendered = self.loader.get(self.playing, spec)
        found = bool(rendered and rendered.found)
        graphic = self.art_mode in ("kitty", "sixel")
        sig = (cols, rows, lay and (lay.left_w, lay.art_cols, lay.art_rows),
               self.playing.path if self.playing else None, found, self.art_mode)
        clear = (cols, rows) != self._size or (graphic and sig != self._art_sig)
        self._size, self._art_sig = (cols, rows), sig

        body = []
        if lay is None:
            body = [(ln, False) for ln in left]
        else:
            pw, lead = lay.panel_w, (lay.panel_w - lay.art_cols) // 2
            sep = ui.paint("│", self.c("dim")) + " "
            info = self.info_lines(pw)
            info_start = lay.art_rows + 1 if lay.art_rows else 0
            for i in range(body_h):
                keep = False
                if i < lay.art_rows:
                    if found and rendered.lines:
                        cell = " " * lead + rendered.lines[i] + " " * (pw - lead - lay.art_cols)
                    elif found:
                        gap = " " * lay.art_cols if clear else f"\033[{lay.art_cols}C"
                        cell = " " * lead + gap + " " * (pw - lead - lay.art_cols)
                        keep = True
                    else:
                        note = ("…" if rendered is None and self.playing else
                                "no cover" if self.playing else "")
                        mid = lay.art_rows // 2
                        cell = ui.paint(fit(f"{note:^{pw}}" if i == mid else "", pw), self.c("dim"))
                else:
                    j = i - info_start
                    cell = info[j] if 0 <= j < len(info) else " " * pw
                body.append((left[i] + sep + cell, keep))

        top = [(self.header(w), False), (ui.paint("─" * w, self.c("dim")), False)]
        bottom = [(ui.paint("─" * w, self.c("dim")), False)] + [(ln, False) for ln in self.now_playing(w)] \
                 + [(self.footer(w), False)]
        out = ["\033[2J" if clear else ""]
        if clear:
            out.append(art.KITTY_DELETE)
        for r, (text, keep) in enumerate((top + body + bottom)[:rows], 1):
            out.append(f"\033[{r};1H{text}" + ("" if keep else "\033[K"))
        out.append("\033[J")
        graphics = ""
        if lay and found and rendered.payload and clear:
            graphics = f"\033[{lay.art_y};{lay.art_x}H" + rendered.payload
        return "".join(out), graphics

    def draw(self):
        cols, rows = shutil.get_terminal_size((80, 24))
        self.cell = art.cell_size()
        text, graphics = self.build_frame(cols, rows)
        if text != self._last_frame or graphics:
            sys.stdout.write(text + graphics)
            sys.stdout.flush()
            self._last_frame = text

                                     
    def run(self):
        self.player.start()
        library.read_tags_in_background(self.all)
        try:
            with keys.Keys() as reader:
                self.reader = reader
                self.art_mode = art.detect_mode(self.images, reader.fd)
                sys.stdout.write(ENTER_SCREEN)
                try:
                    first = random.randrange(len(self.view)) if self.queue.shuffle and self.view else self.cursor
                    self.start_playing(first)
                    while not self.quit:
                        self.drain_events()
                        self.check_sleep()
                        self.draw()
                        k = reader.read(0.12)
                        if k:
                            self.handle_key(k)
                finally:
                    sys.stdout.write(art.KITTY_DELETE + LEAVE_SCREEN)
                    sys.stdout.flush()
        finally:
            self.save_music_config()
            if self.discord:
                self.discord.close()
            self.loader.close()
            self.player.close()