# ♪ sxmply

A growing set of small command-line tools, all under one command: `sxmply <tool>`.

| Tool | What it does |
|---|---|
| `sxmply clip` | Download music or videos from YouTube, Spotify links and any site [yt-dlp](https://github.com/yt-dlp/yt-dlp) supports, with cover art, tags and lyrics |
| `sxmply music` | Terminal music player for your own songs: cover art, lyrics, queue, shuffle, repeat, search, favorites, sleep timer |

More tools will land here over time.

---

# ⚠️ Legal Notice

This tool is intended for personal use only. Downloading videos or music from YouTube, Spotify or other sites may violate their Terms of Service and/or copyright law in your country.

By using this tool, you agree to use it responsibly and not to distribute downloaded content.

The author is not responsible for any misuse or legal consequences.

---

## Screenshots

<img width="900" height="188" alt="image" src="https://github.com/user-attachments/assets/460797d2-3600-46f1-810b-bb6b77da5902" />

## 📦 Installation

Linux with `apt` (Debian/Ubuntu), `dnf` (Fedora) or `pacman` (Arch):

```bash
git clone https://github.com/sxmplyfarhan/Clip-Command.git
cd Clip-Command
chmod +x install.sh
./install.sh
```

The installer only asks for `sudo` to install missing system packages (Python, git, ffmpeg, and mpv for `sxmply music`). Everything else lives in your home folder:

| Path | What |
|---|---|
| `~/.sxmply/` | the code |
| `~/.sxmply/.venv/` | private Python environment with yt-dlp and mutagen |
| `~/.local/bin/sxmply` | the `sxmply` command |
| `~/.config/sxmply/config.json` | your settings (home folders, last format, favorites) |

If `sxmply` isn't found afterwards, add `~/.local/bin` to your `PATH` (the installer tells you how).

**Update:** run `./install.sh` again (it also updates yt-dlp, which you want often, since sites change).
**Remove:** `./install.sh --uninstall`
**Coming from the old `clip` command?** Just run `./install.sh`. It removes the old `clip` launcher and the old `~/.clip-command` folder for you.

## 🎵 sxmply clip

Download music or videos. No accounts, no API keys, no login. Paste a link and it asks what you want:

```
$ sxmply clip https://youtu.be/LgPEyGlUQH8

What do you want?       1. Audio (music)   2. Video
File format             MP3 · M4A · OPUS · FLAC · WAV   (video: MP4 · MKV · WEBM)
Quality / size          320 / 256 / 192 / 128 kbps      (video: best / 1080p / 720p / 480p / 360p)
Save to [~/Music]       Enter keeps the default, or type another folder
```

It remembers your last choice, so next time you can just press Enter through the questions.

```
sxmply clip [-a | -v] [-f FORMAT] [-q QUALITY] [-D DIR] [-y] [--no-lyrics] <link | search [words ...]>
sxmply clip home [DIR | --reset]

  <link>          URL to download (YouTube, Spotify, SoundCloud, ...)
  search [words]  search YouTube; asks what to search for if you give no words
  home [DIR]      show or set the folder downloads go to (--reset to forget it)
  -a              audio only. Always used for Spotify
  -v              video
  -f FORMAT       mp3 m4a opus flac wav | mp4 mkv webm
  -q QUALITY      kbps for audio, max height for video (720, 1080 ...) or 'best'
  -D <dir>        save here this time
  -y              don't ask anything: use the options given, else your last choice
  --no-lyrics     don't look lyrics up online (tags and cover art are still added)
  -h, --help      show help
```

Anything you give on the command line isn't asked again.

```bash
sxmply clip https://youtu.be/LgPEyGlUQH8                    # asks everything
sxmply clip https://youtu.be/LgPEyGlUQH8 -a -f flac         # audio, FLAC, quality needs no question
sxmply clip https://youtu.be/LgPEyGlUQH8 -f mp4 -q 720 -y   # no questions at all
sxmply clip https://open.spotify.com/playlist/XXXXXXXX -D ~/Music
sxmply clip search lofi hip hop
sxmply clip home ~/Music                                    # save here from now on
```

Features:
- Videos and playlists from **YouTube and every other site yt-dlp supports**
- Choose **format and quality (the size knob)** and **where to save** for every download
- **Spotify playlist, album or track** links: songs are matched on YouTube (audio only)
- Interactive YouTube search, coloured output, and a live progress bar with speed and ETA
- Playlist counter (`[3/10]`) and a summary of anything that failed
- **Cover art, tags and lyrics are written into the file**: the thumbnail (cropped square) as the cover, plus title, artist, album, release year and lyrics. `sxmply music` shows all of it
- Lyrics come from [LRCLIB](https://lrclib.net) (free, no account). **Synchronized** lyrics are stored as LRC text in the file's normal lyrics tag (and as an ID3 `SYLT` frame in MP3); if only plain lyrics exist, those are stored. Nothing found? The song is still saved
- Where each thing goes: MP3, M4A, FLAC, OPUS, MP4 and MKV embed the cover. WAV and WEBM can't, so the cover is saved as a `.jpg` next to the file. MKV and WEBM can't hold tags that players read, so their lyrics go in a `.lrc` file next to the video

Notes:
- Playlists ask how many items to download, or `a` for all; the format questions are asked once for the whole batch.
- Album and release year only exist when the site provides them (YouTube Music and Bandcamp do, plain YouTube videos mostly don't). With no release date the upload year is used, which can be later than the song's real year.
- Lyrics are matched by title, artist and length. A song with a very different length on LRCLIB is skipped rather than risk showing another recording's words.
- Lossless formats (FLAC, WAV) have no quality question. WEBM only works when the site offers WebM streams (YouTube does).
- Spotify links must be **public**. Spotify's public page only exposes about the first 100 tracks of a playlist.
- Colours turn off automatically when output is piped, or if you set `NO_COLOR=1`.

### Supported sites

Anything yt-dlp supports (1000+ sites): YouTube, SoundCloud, Bandcamp, Vimeo, Twitch, Dailymotion, Reddit, X/Twitter, TikTok, Instagram, Facebook, Mixcloud, Internet Archive, direct `.mp3`/`.m3u8` links and more. See the [full list](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md).
Spotify links work through the YouTube matching described above. DRM-protected streams are not supported and never will be.

## 🎧 sxmply music

A full-screen player for the songs on your computer. It plays through [mpv](https://mpv.io) (installed by `install.sh`), so it handles mp3, flac, m4a, ogg, opus, wav, aac, wma, mp4, webm and mkv.

```
sxmply music [-s] [-r {off,all,one}] [-F] [--no-recursive] [--images MODE] [--list] [folder | file ...]
sxmply music home [DIR | --reset]
```

```bash
sxmply music                       # plays your music folder
sxmply music ~/Music/Jazz          # a folder (sub-folders included)
sxmply music a.mp3 b.flac          # specific files
sxmply music -s -r all             # start shuffled, repeat everything
sxmply music -F                    # only favorites
sxmply music --images sixel        # force a picture mode (auto, kitty, sixel, ansi, ascii, off)
sxmply music home ~/Music          # remember your music folder
```

With no folder given it plays the `music home` folder, else your `clip home` download folder, else `~/Music`. So after `sxmply clip home ~/Music`, everything you download is already in the player.

**Keys** (press `?` in the player for the same list):

| Key | Action |
|---|---|
| `space` / `p` | pause / play |
| `n` / `b` | next / previous (`b` restarts the song if it has played more than 3 seconds) |
| `←` `→` | seek 5 seconds (hold `Shift` for 30) |
| `↑` `↓` (or `k` `j`), `PgUp` `PgDn`, `g` `G` | move through the list |
| `enter` | play the selected song |
| `s` | shuffle |
| `r` | repeat: off, all, one |
| `+` `-` | volume (remembered next time) |
| `m` | mute |
| `[` `]` | slower / faster playback (0.5x to 2x) |
| `/` | search by title, artist, album or file name. No match? `enter` offers to download it with `sxmply clip` |
| `l` | lyrics view (see below) |
| `i` | show / hide the cover panel |
| `v` | video files: open / close mpv's video window |
| `f` / `F` | heart the selected song / show only hearted songs |
| `t` | sleep timer: 15, 30, 45, 60, 90 minutes or off |
| `c` | jump to the song that is playing (in the lyrics view: follow the song again) |
| `q` / `esc` | quit (`esc` first clears an active search) |

Features:
- Scrolling song list with a live progress bar, volume and speed
- Reads title, artist, album, year and length from the files' tags (needs `mutagen`, which the installer adds)
- **Cover art panel** next to the song list, with title, artist, album, year and format underneath
- **Lyrics view** (`l`): synchronized lyrics follow the song, with the current line highlighted; plain lyrics just scroll (`↑` `↓`)
- **Search fallback**: search for a song you don't have, press `enter`, and it asks `Song not found. Download via sxmply clip? (y/N)`. On `y` it runs `sxmply clip search <what you typed>` (you pick the result and the audio/video format, quality), saves into your music folder, adds the file to the list and plays it
- Search that narrows the list as you type; the queue follows what you see
- Favorites that are remembered between runs
- Skips files that can't be played, and stops cleanly at the end of the queue
- Works on Linux and macOS. Windows isn't supported by the player yet.

### Cover art, lyrics and video

**Where a cover comes from:** inside the file, else an image next to it (`song.jpg`, or `cover` / `folder` / `front` in the folder), else, for videos, a frame from the video. It needs `ffmpeg` (installed with `sxmply`).

**How it is drawn.** The player asks your terminal what it supports when it starts:

| Mode | Terminals | Notes |
|---|---|---|
| `kitty` | kitty, WezTerm, Ghostty, Konsole | real image |
| `sixel` | foot, mlterm, xterm (`-ti vt340`), Windows Terminal, iTerm2 (sixel on), ... | real image |
| `ansi` | nearly everything | coloured half-block characters; truecolor if `COLORTERM` says so, else 256 colours |
| `ascii` | `NO_COLOR` / `TERM=dumb` | plain characters |

Force one with `--images MODE` or `SXMPLY_IMAGES=MODE`; `--images off` hides the picture. Inside `tmux` or `screen` it uses `ansi` (graphics need tmux's pass-through): pick `--images kitty` or `sixel` yourself if you have set that up.
The panel appears when the terminal is about 70 columns wide and 15 rows tall; `i` hides it.

**Lyrics** are read from the file (MP3/WAV `SYLT` and `USLT`, M4A `©lyr`, FLAC/OPUS `LYRICS`), else from a `.lrc` or `.txt` with the same name next to the song, so you can add your own.

**Video files** (`.mp4`, `.mkv`, `.webm`) play as audio inside the terminal, with the cover or a frame from the video in the panel. Press `v` to open mpv's own video window; it needs a graphical session (`$DISPLAY` / Wayland), otherwise the player tells you and keeps playing the audio.

## 🗂 Project layout

```
bin/sxmply            entry point
sxmply/
  cli.py              `sxmply <tool>`: picks the tool and runs it
  ui.py               shared: colours, prompts, menus, progress bar
  config.py           shared: settings file and the `home` commands
  lrc.py              shared: synchronized / plain lyrics parser
  clip/               the `clip` tool
    cli.py            arguments and main flow
    formats.py        format/quality choices and the questions asked
    downloader.py     everything that talks to yt-dlp (cover art options)
    metadata.py       tags + lyrics lookup (LRCLIB) written into the file
    spotify.py        Spotify link -> track list
    search.py         interactive YouTube search
  music/              the `music` tool
    cli.py            arguments and startup
    app.py            the full-screen interface and key handling
    player.py         controls mpv through its IPC socket
    playlist.py       the queue: shuffle and repeat
    library.py        finds songs and reads their tags
    art.py            cover art: find, decode (ffmpeg), draw (Kitty / Sixel / ANSI)
    lyrics.py         reads lyrics from the file or a .lrc next to it
    keys.py           single key presses from the terminal
```

**Adding a new tool:** make a folder `sxmply/<name>/` with a `cli.py` that has a `main(argv)` function, then add one line to `COMMANDS` in `sxmply/cli.py`. Shared helpers go in `sxmply/ui.py` and `sxmply/config.py`.

## ❓ FAQ

**When macOS and Windows?** Soon, once the installer is ported. `sxmply clip` is platform-neutral already, and `sxmply music` runs on macOS if you install `mpv`, `ffmpeg` and `mutagen` yourself. The music player doesn't support Windows yet.
**What about Android and iOS?** Not planned. It would be a hassle.
**Why does this exist?** I didn't want to use a sketchy website, and I didn't want to type a complex yt-dlp command.

## 📄 License

[MIT](LICENSE). See [CHANGELOG.md](CHANGELOG.md) for what changed between versions.
