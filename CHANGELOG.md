# Changelog

## v0.5.0: cover art, lyrics and search-to-download in `sxmply music`

### Added
- **Search fallback.** In `sxmply music`, search with `/` and press `enter` on a search that matches nothing: it asks `Song not found. Download via sxmply clip? (y/N)`. `y` runs `sxmply clip search <your words>` (you choose the result, audio or video, format and quality), saves into the folder you are playing (else your `music home` / `clip home` / `~/Music`), adds the new file to the list and plays it.
- **Cover art in `sxmply music`.** A panel beside the list shows the current song's cover with its title, artist, album, year, format and whether it has lyrics. Drawn with the Kitty graphics protocol or Sixel when the terminal supports them (detected automatically), otherwise as coloured half-block text, or plain ASCII with `NO_COLOR`. `--images MODE` / `SXMPLY_IMAGES` override it; `i` hides the panel. Covers are decoded by ffmpeg in the background, so no new Python dependency and no waiting.
- **Lyrics view** (`l`). Synchronized lyrics follow the song with the current line highlighted (`↑`/`↓` scroll, `c` follows again); plain lyrics scroll. Read from the file (ID3 `SYLT`/`USLT`, MP4 `©lyr`, Vorbis `LYRICS`) or from a `.lrc` / `.txt` next to it.
- **Video files.** Cover art for a video is its embedded picture, else a frame from the video. `v` opens or closes mpv's video window; with no graphical session the player says so and keeps playing the audio.
- **`sxmply clip` now writes cover art, tags and lyrics into downloads.** The thumbnail is cropped square and embedded (MP3, M4A, FLAC, OPUS, MP4, MKV; WAV and WEBM get a `.jpg` next to the file). Title, artist, album and release year are cleaned up from what the site provides ("Artist - Title (Official Video)" becomes artist and title). Lyrics come from LRCLIB; synchronized ones are stored as LRC text (plus `SYLT` in MP3). MKV/WEBM lyrics go to a `.lrc` file. New `--no-lyrics` option.
- `sxmply/lrc.py`, a small shared lyrics parser (timestamps, `[offset:]`, several stamps per line, enhanced word tags).

### Changed
- `sxmply clip` options after `--` are now treated as plain words (`sxmply clip search -- -weird name`). Python's intermixed argument parser didn't handle `--`.
- Video downloads now get title/artist metadata too.
- `Track` has a `year`, and `sxmply music --help` documents the new keys.

### Known limitations (please try them)
- **Not run against the real thing.** Written and tested without network access, without real `mpv`, `yt-dlp` or `mutagen`. Tested: cover finding and decoding on real MP3/M4A/FLAC/OPUS/MKV/MP4 files (ffmpeg), the Sixel encoder (decoded back, pixel-exact), Kitty chunking, the whole player screen and run loop in a pseudo-terminal against a stand-in mpv (including the terminal capability probe), the search fallback flow, the LRC parser, tag guessing, and the LRCLIB code against mocked replies. **Not tested:** a real download through yt-dlp's cover-art post-processors, real LRCLIB responses, tag writing/reading through mutagen, and mpv's video window (`vid` switched at run time).
- Kitty/Sixel need the terminal to answer the start-up query; inside tmux/screen use `--images` to force them.
- Cover art inside MKV is only found when stored as an attachment; otherwise the player falls back to a video frame.
- There is no key yet to fetch lyrics for songs you downloaded before v0.5.0 (add a `.lrc` next to them, or download again).

## v0.4.0: `sxmply music`, and `sxmply clip` asks what you want

### Added
- **`sxmply music`**, a full-screen terminal music player for your own files (it grows out of Tune-CLI):
  - Plays mp3, flac, m4a, ogg, opus, wav, aac, wma, mp4, webm and mkv through mpv. Folders are scanned recursively.
  - Scrolling song list, live progress bar, volume and speed in the status line.
  - Everything Tune-CLI had: pause/play, next/previous, seek, shuffle, repeat (off / all / one) and a default folder (`sxmply music home DIR`).
  - New: volume and mute (volume is remembered), playback speed, search-as-you-type, favorites (and a favorites-only view), a sleep timer, jump to the playing song, a help screen (`?`), and `--list`.
  - Reads title, artist, album and length from tags when `mutagen` is installed. Skips files that can't be played.
  - With no folder given it uses the `music home` folder, else the `clip home` folder, else `~/Music`.
  - Linux and macOS. Not supported on Windows yet.
- **`sxmply clip` now asks before every download:** audio or video, file format, quality (the size knob) and where to save.
  - Audio: mp3, m4a, opus, flac, wav at 320/256/192/128 kbps (lossless formats have no bitrate question).
  - Video: mp4, mkv, webm, best or up to 1080p/720p/480p/360p.
  - Your last choice becomes the default next time. Playlists ask once for the whole batch.
  - New options to skip questions: `-f FORMAT`, `-q QUALITY`, and `-y` (no questions at all). `-a` / `-v` / `-D` still work.
- **`sxmply clip home DIR`** sets the folder downloads are saved to. `sxmply clip home` shows it and `--reset` forgets it.
- **`sxmply/config.py`**, a small shared settings file at `~/.config/sxmply/config.json`.
- Downloaded audio now gets title/artist tags written into the file.

### Changed
- Without `-D`, downloads go to your `clip home` folder if set, else the current folder (you are asked to confirm).
- Running `sxmply clip <link>` with no `-a`/`-v` now asks audio or video (before, it silently picked video).
- The installer also installs `mpv` (a failure there is only a warning) and `mutagen`.
- Shared `ui.py` gained `menu()`, `ask_default()` and a reverse-video style.

### Known limitations
- Unlike Tune-CLI, `↑`/`↓` move the selection in the list instead of changing track. Use `n` / `b` for next / previous.
- The player was tested against a simulated mpv, not yet against a real one with real music. Please try it.
- WEBM video only works for sources that offer WebM streams.

## v0.3.0: the project becomes `sxmply`, the downloader becomes `sxmply clip`

### Added
- **`sxmply` command** that runs tools by name: `sxmply <tool> ...`. `sxmply` alone lists the tools, `sxmply --version` prints the version, and a mistyped tool gets a "Did you mean…" hint.
- **`sxmply clip search [words]`** to search YouTube. Give the words to search straight away, or leave them out and it asks.
- **Easy to extend:** a new tool is a folder `sxmply/<name>/` with a `main(argv)` function plus one line in `COMMANDS` in `sxmply/cli.py`.
- Options can now go before or after the link or search words (`sxmply clip search lofi -D ~/Music`).

### Changed
- **The command is now `sxmply clip ...`** (it was `clip ...`).
- **Folders and files:** `clip` → `bin/sxmply`; `clipcmd/` → `sxmply/` with the downloader in `sxmply/clip/`. `ui.py` stays shared at `sxmply/ui.py`.
- **Help text:** running `sxmply clip` with no arguments shows help, and the help now says how to search (`search`) instead of "leave out the link", which never worked.
- **Install location:** `~/.sxmply` (was `~/.clip-command`) and launcher `~/.local/bin/sxmply` (was `~/.local/bin/clip`).
- **Installer:** the repo URL can be overridden with `SXMPLY_REPO_URL` (was `CLIP_REPO_URL`).
- **README** rewritten around `sxmply` with a tools table and a "how to add a tool" section.

### Removed
- **The `clip` command** and the old `clipcmd/` package name. `./install.sh` deletes the old `clip` launcher, the old `~/.clip-command` folder and the v0.1 `/usr/local/bin/clip` link.
- **The "No link given. Search YouTube instead? (y/n)" prompt.** Searching is now an explicit command.

### Upgrading from v0.2
Run `./install.sh`, then use `sxmply clip ...` instead of `clip ...`.

## v0.2.0 (compared with the original single-file version)

### Added
- **Modular code.** The 340-line `clip` script is now a 13-line entry point plus a `clipcmd/` package: `cli.py`, `ui.py`, `downloader.py`, `spotify.py`, `search.py`.
- **Colours and a nicer prompt.** Coloured messages (`›` info, `✔` success, `!` warning, `✘` error), headings, and prompts like `? How many videos? (1-3, or 'a' for all) ›`. Colours switch off automatically when piped or when `NO_COLOR` is set.
- **New progress bar.** Computed from real byte counts (the old one parsed yt-dlp's formatted strings). Shows speed and ETA, plus a "Converting…" line during MP3 conversion.
- **Spotify without a login.** Tracks are read from Spotify's public embed page. Playlists, albums and single tracks are supported.
- **Any site.** Every non-Spotify link is passed to yt-dlp, which supports 1000+ sites and detects playlists by itself.
- **Download counter and failure summary.** Playlists show `[n/total]` and end with a list of anything that failed.
- **Proper argument parsing** with `argparse`: real `--help`, and `-a` / `-v` can't be combined.
- **Installer rewrite** (see below): per-user install, private virtual environment, update and `--uninstall` support, automatic removal of the old v0.1 link.
- **`CHANGELOG.md`** (this file).

### Changed
- **Installer.** Old: installed Spotipy from source and a standalone yt-dlp binary into `/usr/local/bin`, built `gcc`/`make` dependencies, installed the `yay` AUR helper on Arch, and symlinked `clip` into `/usr/local/bin` with `sudo`. New: installs only missing system packages (Python, git, ffmpeg), puts yt-dlp in `~/.clip-command/.venv`, and creates `~/.local/bin/clip`. Re-running it updates both the code and yt-dlp.
- **License.** CC BY-NC-SA 4.0 → MIT. CC licenses are not meant for software (no warranty disclaimer or patent language, and NonCommercial isn't open source). **MIT allows commercial use.** If you want to keep NonCommercial, use PolyForm Noncommercial 1.0.0 instead.
- **README** rewritten: no login instructions, supported sites, new install and update steps, project layout.
- **Help text** now comes from `argparse`. The legal notice is kept at the bottom.
- **Spotify matching** still uses `ytsearch1:` on YouTube, as before.
- **Playlist prompts** (YouTube and Spotify) share one function instead of two copies.

### Removed
- **`clip login`** and the whole Spotify credentials flow (Client ID / Secret, `~/.config/clip/clip_credentials.json`).
- **Spotipy dependency.** yt-dlp is now the only Python dependency.
- **`config.py`** (only existed for the login).
- **Install-time requirements** that were never needed: `make`, `gcc`, `pkg-config`, `curl`, `python3-venv` on Fedora (the package doesn't exist there), `yay`, and the `python3 setup.py install` step (deprecated).
- **Unused code:** `clean_link()`, the unused `-v` variable (`-v` now simply means the default video mode), and the unused `video_only` flag.

### Fixed
- `clip -D ~/Music <url>` used the folder as the link, because the first argument without a dash was assumed to be the link.
- `-v` was parsed but never used.
- A Ctrl-C or Ctrl-D at any prompt now exits cleanly.
- The credentials file (v0.1) was saved world-readable. It no longer exists; `./install.sh --uninstall` deletes any left over from v0.1.

### Known limitations
- Spotify's public page shows about the first 100 tracks of a playlist, and private playlists can't be read. This is the price of no login.
- The Spotify page reader depends on Spotify's page layout, which is unofficial and can change.
- Linux only (`apt`, `dnf`, `pacman`).
- Not yet tested against live YouTube and Spotify. Please try one of each.

### Upgrading from v0.1
1. Run `./install.sh` (it removes the old `/usr/local/bin/clip` link for you).
2. Optional: delete `~/.config/clip/` (old Spotify keys).
