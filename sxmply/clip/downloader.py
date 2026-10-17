                                                                           
import os

import yt_dlp

from .. import ui
from . import formats, metadata


def video_selector(fmt, height):
                                                                                
    h = f"[height<={height}]" if height and height != "best" else ""
    if fmt == "mp4":
        return (f"bestvideo{h}[ext=mp4]+bestaudio[ext=m4a]/best{h}[ext=mp4]"
                f"/bestvideo{h}+bestaudio/best{h}")
    if fmt == "webm":
                                                                                 
        return f"bestvideo{h}[ext=webm]+bestaudio[ext=webm]/best{h}[ext=webm]"
    return f"bestvideo{h}+bestaudio/best{h}"                             


def build_opts(settings):
    opts = {
        "progress_hooks": [ui.progress_hook],
        "postprocessor_hooks": [ui.postprocess_hook],
        "outtmpl": os.path.join(settings.save_path, "%(title)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "writethumbnail": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios"]
            }
        },
    }
    embed_cover = settings.fmt in metadata.EMBED_COVER
    pps = [
                                                                                          
        {"key": "FFmpegThumbnailsConvertor", "format": "jpg", "when": "before_dl"},
    ]
    if settings.audio:
        codec, lossy = formats.AUDIO[settings.fmt]
        extract = {"key": "FFmpegExtractAudio", "preferredcodec": codec}
        if lossy and settings.quality:
            extract["preferredquality"] = settings.quality
        opts["format"] = "bestaudio/best"
        pps += [extract]
    else:
        opts["format"] = video_selector(settings.fmt, settings.quality)
        opts["merge_output_format"] = settings.fmt
                                                                                   
                                                                        
    pps.append({"key": "FFmpegMetadata", "add_metadata": True})
    if embed_cover:
        pps.append({"key": "EmbedThumbnail", "already_have_thumbnail": False})
    opts["postprocessors"] = pps

    quiet_ffmpeg = ["-loglevel", "error"]
    opts["postprocessor_args"] = {
        "default": quiet_ffmpeg,
                                                                             
        "thumbnailsconvertor+ffmpeg_o": quiet_ffmpeg + [
            "-c:v", "mjpeg", "-q:v", "2",
            "-vf", "crop='min(iw,ih)':'min(iw,ih)'"],
    }
    return opts


def _final_path(ydl, info, settings):
                                                                                          
    for d in info.get("requested_downloads") or []:
        if d.get("filepath") and os.path.exists(d["filepath"]):
            return d["filepath"]
    guess = os.path.splitext(ydl.prepare_filename(info))[0] + "." + settings.fmt
    return guess if os.path.exists(guess) else None


def download(link, settings):
                                                                               
    os.makedirs(settings.save_path, exist_ok=True)
    try:
        with yt_dlp.YoutubeDL(build_opts(settings)) as ydl:
            info = ydl.extract_info(link, download=True)
            if info and info.get("entries"):                                                         
                info = next((e for e in info["entries"] if e), None)
            path = _final_path(ydl, info, settings) if info else None
    except yt_dlp.utils.DownloadError as e:
        print()
        ui.error(f"Download error: {e}")
        return None
    if path:
        metadata.finalize(path, info, settings)
    return path


def get_playlist_info(link):
                                                                                   
    opts = {"quiet": True, "no_warnings": True, "extract_flat": True, "skip_download": True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(link, download=False)
    except yt_dlp.utils.DownloadError as e:
        ui.error(f"Couldn't read that link: {e}")
        return None
    entries = [e for e in (info.get("entries") or []) if e]
    return {
        "id": info.get("id"),
        "title": info.get("title"),
        "total": len(entries),
        "titles": [e.get("title") or "(untitled)" for e in entries[:5]],
        "entries": entries,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios"]
            }
        },
    }


def entry_url(entry):
    return entry.get("url") or entry.get("webpage_url")
