<div align="center">

# sxmply

**A modern, lightning-fast suite of command-line audio tools.**  
*Download anything with embedded tags & lyrics, then play it in a full-featured terminal dashboard.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Linux | macOS](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS-teal.svg)](#-supported-platforms)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Engine: mpv & yt-dlp](https://img.shields.io/badge/Engines-mpv%20%7C%20yt--dlp-ff69b4.svg)](#)

</div>

---

## 🗂 Tools at a Glance

| Command | Description |
|---|---|
| **`sxmply clip`** | Download audio/video from YouTube, Spotify, and 1000+ sites with embedded square cover art, metadata tags, and synchronized lyrics. |
| **`sxmply music`** | Full-screen terminal music player with responsive table columns, Kitty/Sixel cover art, live synchronized lyrics, audio visualizer, Discord RPC, and playlists. |

---

## 📸 Screenshots

<div align="center">
  <img width="900" alt="sxmply-banner" src="https://github.com/user-attachments/assets/460797d2-3600-46f1-810b-bb6b77da5902" />
</div>

<br>

---

## ✨ Features

### 🎧 `sxmply music`
- **Structured Table Layout:** Responsive columns (`#`, `TITLE`, `ARTIST`, `ALBUM`, `YEAR`, `TIME`, `♥`) that automatically adapt to any terminal width.
- **Synchronized Live Lyrics (`l`):** Displays timestamps (`0:02 ▶ ...`), highlights the current line in vibrant colors, dims past lines, and centers the lyrics smoothly as the song plays.
- **On-Demand Lyric Fetcher (`u`):** Missing lyrics on an older track? Press `u` to instantly search LRCLIB in the background and save them to `.lyrics/`.
- **Integrated Audio Visualizer:** Real-time dancing spectrum meters on both the now-playing bar and side panel.
- **Native Discord Rich Presence (RPC):** Shows your current song, artist, album, live playback timer, and play/pause state on Discord (zero extra libraries needed).
- **Full Playlist Manager (`P`):** 
  - Switch between All Tracks, Favorites, and custom playlists.
  - Create (`n`), rename (`r`), or delete (`d`) playlists.
  - Add or toggle songs from any view (`a`).
  - Reorder songs live inside playlists using `Shift+↑` / `Shift+↓` (or `K` / `J`).
- **Cover Art in the Terminal:** Supports Kitty graphics protocol, Sixel graphics, ANSI half-blocks, and ASCII.
- **Search-to-Download Fallback:** Search for a song with `/`. If it's not in your library, press `Enter` to download it directly via `sxmply clip` and play it immediately.
- **100% Customizable:** Custom keybinds and theme colors configured in `~/.config/sxmply/music/config.json`.

---

### 🎵 `sxmply clip`
- **Any Site Supported:** YouTube, Spotify links are completly supported but other sites will probably work unless they require cookies.
- **Automatic Tagging & Cover Art:** Automatically writes title, artist, album, and release year into the file, and crops thumbnails into square cover art.
- **Clean Lyrics Storage:** Synchronized lyrics are written into audio tags and backed up inside a hidden `.lyrics/` folder, keeping your music directory free from loose `.lrc` clutter.
- **Format Choices:** Audio (`mp3`, `m4a`, `opus`, `flac`, `wav`) or Video (`mp4`, `mkv`, `webm`) with selectable bitrates and resolutions.

---

## 💻 Supported Platforms

Theoretically any platform is supported, you just need to install the right prerequesties.
Just make sure to have git,python3,ffmeg,mpv installed and than run the install.sh

---

## 📦 Installation

### 1. Prerequisites

Make sure you have `git`, `python3`, `ffmpeg`, and `mpv` installed on your machine:

---

### 2. Install `sxmply`

Clone the repository and run the setup script (from default, arch, debian and fedora are supported.:

```bash
git clone https://github.com/sxmplyfarhan/Clip-Command.git
cd Clip-Command
chmod +x install.sh
./install.sh
```

Everything installs cleanly into your user home directory:
* `~/.sxmply/` — application source code & isolated virtual environment
* `~/.local/bin/sxmply` — system executable link
* `~/.config/sxmply/` — settings, playlists, themes, and default folders

> **Tip:** If `sxmply` is not recognized after install, ensure `~/.local/bin` is in your `PATH`:
> ```bash
> echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc # or ~/.zshrc
> source ~/.bashrc # or ~/.zshrc
> ```

* **Update:** Re-run `./install.sh` (this also keeps `yt-dlp` up to date).
* **Uninstall:** Run `./install.sh --uninstall`.

---

## 🎵 Usage: `sxmply clip`

Download audio or video by passing a URL or search phrase:

```bash
# Interactive mode (prompts for format, quality, and location)
sxmply clip https://youtu.be/dQw4w9WgXcQ

# Quick audio download in FLAC
sxmply clip https://youtu.be/dQw4w9WgXcQ -a -f flac

# Silent mode: use defaults without questions
sxmply clip https://youtu.be/dQw4w9WgXcQ -f mp3 -q 320 -y

# Download a public Spotify playlist directly into your music directory
sxmply clip https://open.spotify.com/playlist/XXXXXXXX -D ~/.config/sxmply/music

# Search YouTube interactively
sxmply clip search lofi hip hop

# Change the default download folder
sxmply clip home ~/Music
sxmply clip home --reset   # Resets back to ~/.config/sxmply/clip
```

---

## 🎧 Usage: `sxmply music`

Launch the terminal music player:

```bash
sxmply music                      # Plays your default music directory
sxmply music ~/Music/Jazz         # Plays a specific folder (recursive)
sxmply music song.mp3 other.flac  # Plays specific files
sxmply music -s -r all            # Starts shuffled, repeat-all enabled
sxmply music -F                   # Plays favorites only
sxmply music --images kitty       # Force picture mode (auto, kitty, sixel, ansi, off)

# Change default player folder
sxmply music home ~/Music
sxmply music home --reset         # Resets back to ~/.config/sxmply/music
```

### ⌨️ Default Keybindings

| Key | Action |
|:---|:---|
| `space` / `p` | **Pause / Play** |
| `n` / `b` | **Next / Previous track** *(restarts track if >3s in)* |
| `←` / `→` | **Seek backward / forward 5s** *(hold `Shift` for 30s)* |
| `↑` / `↓` *(or `k` / `j`)* | **Navigate up / down** |
| `PgUp` / `PgDn` | **Scroll page up / down** |
| `home` / `end` *(or `g` / `G`)* | **Jump to top / bottom** |
| `enter` | **Play selected song** / Confirm selection |
| `c` | **Jump cursor to currently playing track** |
| `s` / `r` | **Toggle Shuffle** / **Cycle Repeat** *(off ➔ all ➔ one)* |
| `+` / `-` / `m` | **Volume up / down** / **Toggle mute** |
| `[` / `]` | **Playback speed** *(0.5x – 2.0x)* |
| `l` | **Toggle Live Lyrics view** |
| `u` | **Fetch lyrics on-demand** from LRCLIB for the selected song |
| `P` *(Shift+P)* | **Open Playlists Browser** |
| `a` | **Add selected song to a playlist** |
| `x` / `delete` | **Remove song from playlist** *(or delete custom playlist)* |
| `Shift+↑` / `Shift+↓` *(or `K` / `J`)* | **Move song up / down** inside custom playlist |
| `f` / `F` | **Heart favorite (♥)** / **Filter favorites only** |
| `i` / `v` | **Toggle Cover Art panel** / **Open mpv video window** |
| `/` | **Search library** *(Enter on empty results prompts to download)* |
| `t` | **Sleep timer** *(15, 30, 45, 60, 90 mins or off)* |
| `?` | **Open Help card** |
| `q` / `esc` | **Quit** / Clear active prompt or search |

---

## 🎨 Customization

`sxmply` uses dedicated, decoupled JSON configurations located in `~/.config/sxmply/`:

```text
~/.config/sxmply/
├── clip/
│   └── config.json       <-- Download directory & format memory
└── music/
    └── config.json       <-- Keybinds, colors, playlists & volume
```

### Changing Colors & Keybinds
Open `~/.config/sxmply/music/config.json` to customize your theme and shortcuts:

```json
{
  "music_dir": "~/.config/sxmply/music",
  "volume": 75,
  "discord_rpc": true,
  "theme": {
    "primary": "magenta",
    "accent": "cyan",
    "playing": "green",
    "cursor": "reverse",
    "dim": "gray",
    "highlight": "yellow",
    "heart": "magenta"
  },
  "keybinds": {
    "play_pause": ["space", "p"],
    "next": ["n"],
    "prev": ["b"],
    "lyrics": ["l"],
    "fetch_lyrics": ["u"],
    "playlists": ["P"],
    "add_to_playlist": ["a"],
    "move_up": ["K", "S-up"],
    "move_down": ["J", "S-down"]
  }
}
```

*Colors supported:* `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `gray`, `bold`, `dim`, `reverse`.

---

## 🗂 Project Structure

```text
bin/
  sxmply                  # CLI Entry point launcher
sxmply/
  cli.py                  # Command dispatcher
  config.py               # Settings manager (clip & music configs)
  lrc.py                  # Synchronized & plain lyrics parser
  ui.py                   # Terminal themes, ANSI formatting & progress bars
  clip/
    cli.py                # sxmply clip arguments & flow
    downloader.py         # yt-dlp wrapper & thumbnail embedder
    formats.py            # Format/quality choices & interactive menus
    metadata.py           # LRCLIB lyrics lookup, tagger, .lyrics/ sidecar
    search.py             # Interactive YouTube search
    spotify.py            # Public Spotify track list parser
  music/
    app.py                # Main TUI dashboard, table layout, visualizer & RPC
    art.py                # Kitty, Sixel, ANSI cover art renderer
    cli.py                # sxmply music options & startup
    keys.py               # Raw terminal input handler
    library.py            # Audio file discovery & metadata scanner
    lyrics.py             # Lyrics loader (embedded tags & .lyrics/ folder)
    player.py             # mpv IPC client
    playlist.py           # Play queue, shuffle, and repeat logic
```

---

## ⚠️ Legal Notice

This software is for personal use only. Downloading media from third-party services may violate their Terms of Service and/or applicable copyright laws. Please use this tool responsibly and support artists by purchasing their music and merchandise.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
