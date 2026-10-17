\
\
\
\
\
   
import json
import os

from . import ui


def base_dir():
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    p = os.path.join(base, "sxmply")
    os.makedirs(p, exist_ok=True)
    return p


def tool_dir(tool):
    p = os.path.join(base_dir(), tool)
    os.makedirs(p, exist_ok=True)
    return p


def default_dir(tool):
                                                                  
    return tool_dir(tool)


def config_path(tool):
    return os.path.join(tool_dir(tool), "config.json")


def _migrate_old_config():
                                                                                             
    old_file = os.path.join(base_dir(), "config.json")
    if not os.path.isfile(old_file):
        return
    try:
        with open(old_file, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
                            
            clip_data = load("clip")
            if "clip_dir" in data:
                clip_data["download_dir"] = data["clip_dir"]
            if "clip_last" in data:
                clip_data["last_choices"] = data["clip_last"]
            save(clip_data, "clip")

                             
            music_data = load("music")
            if "music_dir" in data:
                music_data["music_dir"] = data["music_dir"]
            if "music_volume" in data:
                music_data["volume"] = data["music_volume"]
            if "favorites" in data:
                music_data["favorites"] = data["favorites"]
            if "playlists" in data:
                music_data["playlists"] = data["playlists"]
            save(music_data, "music")

        os.rename(old_file, old_file + ".bak")
    except Exception:
        pass


def load(tool):
                                                                  
    _migrate_old_config()
    p = config_path(tool)
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save(data, tool):
                                 
    tool_dir(tool)
    target = config_path(tool)
    tmp = target + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, target)


def get(key, default=None, tool="music"):
    return load(tool).get(key, default)


def set(key, value, tool="music"):              
    data = load(tool)
    data[key] = value
    try:
        save(data, tool)
    except OSError as e:
        ui.warn(f"Couldn't save settings ({e}).")


def unset(key, tool="music"):
    data = load(tool)
    if key in data:
        del data[key]
        try:
            save(data, tool)
        except OSError as e:
            ui.warn(f"Couldn't save settings ({e}).")


def resolve_dir(text):
    return os.path.abspath(os.path.expanduser(text.strip()))


def home_command(tool, key, words, label, cmd, create, reset=False):
                                                               
    if reset:
        unset(key, tool=tool)
        def_path = default_dir(tool)
        ui.success(f"The {label} folder is reset to {ui.paint(def_path, 'cyan')}")
        return

    if not words:
        current = get(key, tool=tool) or default_dir(tool)
        ui.info(f"The {label} folder is {ui.paint(current, 'cyan')}")
        ui.info(f"Change it with: {cmd} <folder>   (or {cmd} --reset)")
        return

    path = resolve_dir(" ".join(words))
    if create:
        try:
            os.makedirs(path, exist_ok=True)
        except OSError as e:
            ui.error(f"Couldn't create {path}: {e}")
            raise SystemExit(1)
    elif not os.path.isdir(path):
        ui.error(f"{path} is not a folder.")
        raise SystemExit(1)
    set(key, path, tool=tool)
    ui.success(f"The {label} folder is now {ui.paint(path, 'cyan')}")