#!/usr/bin/env bash
# sxmply installer.
#   ./install.sh              install, or update an existing install
#   ./install.sh --uninstall  remove everything this script created
#
# Layout it creates (nothing outside your home folder, except system packages):
#   ~/.sxmply/                the code (git clone)
#   ~/.sxmply/.venv/          private Python environment holding yt-dlp and mutagen
#   ~/.local/bin/sxmply       launcher you run as `sxmply`
set -euo pipefail

REPO_URL="${SXMPLY_REPO_URL:-https://github.com/sxmplyfarhan/Clip-Command.git}"
INSTALL_DIR="$HOME/.sxmply"
VENV_DIR="$INSTALL_DIR/.venv"
BIN_DIR="$HOME/.local/bin"
LAUNCHER="$BIN_DIR/sxmply"

# Locations used by earlier versions (when the command was just `clip`)
OLD_DIR="$HOME/.clip-command"
OLD_LAUNCHER="$BIN_DIR/clip"
OLD_LINK="/usr/local/bin/clip"

# ===== OUTPUT =====
if [ -t 1 ]; then B=$'\033[1m'; G=$'\033[32m'; Y=$'\033[33m'; R=$'\033[31m'; N=$'\033[0m'; else B=""; G=""; Y=""; R=""; N=""; fi
say()  { printf '%s›%s %s\n' "$B" "$N" "$*"; }
ok()   { printf '%s✔%s %s\n' "$G" "$N" "$*"; }
warn() { printf '%s!%s %s\n' "$Y" "$N" "$*"; }
die()  { printf '%s✘%s %s\n' "$R" "$N" "$*" >&2; exit 1; }

# True if the file is a launcher this installer wrote for the old folder.
is_old_launcher() { [ -f "$OLD_LAUNCHER" ] && grep -q "$OLD_DIR" "$OLD_LAUNCHER"; }

# ===== UNINSTALL =====
if [ "${1:-}" = "--uninstall" ]; then
    rm -f "$LAUNCHER"
    if is_old_launcher; then rm -f "$OLD_LAUNCHER"; fi
    rm -rf "$INSTALL_DIR" "$OLD_DIR"
    rm -rf "$HOME/.config/clip"   # credentials file left by v0.1 (login was removed in v0.2)
    ok "sxmply removed."
    exit 0
fi

# ===== PACKAGE MANAGER =====
PM=""
if   command -v apt    >/dev/null 2>&1; then PM="apt"
elif command -v dnf    >/dev/null 2>&1; then PM="dnf"
elif command -v pacman >/dev/null 2>&1; then PM="pacman"
fi

# ===== SYSTEM DEPENDENCIES (only what is missing) =====
need=()
command -v python3 >/dev/null 2>&1 || need+=(python3)
command -v git     >/dev/null 2>&1 || need+=(git)
command -v ffmpeg  >/dev/null 2>&1 || need+=(ffmpeg)
python3 -c 'import venv, ensurepip' >/dev/null 2>&1 || need+=(venv)

if [ "${#need[@]}" -gt 0 ]; then
    [ -n "$PM" ] || die "Missing: ${need[*]}. Unsupported distro, please install them manually and re-run."
    say "Installing system packages (needs sudo): ${need[*]}"
    case "$PM" in
        apt)
            sudo apt update
            sudo apt install -y python3 python3-venv git ffmpeg
            ;;
        dnf)
            sudo dnf install -y python3 git
            command -v ffmpeg >/dev/null 2>&1 || sudo dnf install -y ffmpeg || sudo dnf install -y ffmpeg-free
            ;;
        pacman)
            sudo pacman -S --needed --noconfirm python git ffmpeg
            ;;
    esac
fi

# ===== mpv (only needed by `sxmply music`, so a failure here is not fatal) =====
if ! command -v mpv >/dev/null 2>&1; then
    if [ -n "$PM" ]; then
        say "Installing mpv for 'sxmply music' (needs sudo)"
        case "$PM" in
            apt)    sudo apt install -y mpv    || warn "Couldn't install mpv. 'sxmply clip' still works; install mpv later for 'sxmply music'." ;;
            dnf)    sudo dnf install -y mpv    || warn "Couldn't install mpv (on Fedora it comes from RPM Fusion). 'sxmply clip' still works." ;;
            pacman) sudo pacman -S --needed --noconfirm mpv || warn "Couldn't install mpv. 'sxmply clip' still works." ;;
        esac
    else
        warn "mpv not found. Install it to use 'sxmply music' ('sxmply clip' works without it)."
    fi
fi

# ===== CODE: CLONE OR UPDATE =====
if [ -d "$INSTALL_DIR/.git" ]; then
    say "Updating sxmply…"
    git -C "$INSTALL_DIR" pull --ff-only
elif [ -e "$INSTALL_DIR" ]; then
    die "$INSTALL_DIR exists but is not an sxmply checkout. Move it away and re-run."
else
    say "Downloading sxmply…"
    git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
fi

# ===== PYTHON ENVIRONMENT (yt-dlp for `clip`, mutagen for song tags in `music`) =====
[ -x "$VENV_DIR/bin/python" ] || python3 -m venv "$VENV_DIR"
say "Installing / updating yt-dlp and mutagen…"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip yt-dlp mutagen

# ===== LAUNCHER =====
mkdir -p "$BIN_DIR"
cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
exec "$VENV_DIR/bin/python" "$INSTALL_DIR/bin/sxmply" "\$@"
EOF
chmod +x "$LAUNCHER"

# ===== CLEAN UP OLDER VERSIONS (the command used to be `clip`) =====
if is_old_launcher; then
    say "Removing old 'clip' launcher ($OLD_LAUNCHER)"
    rm -f "$OLD_LAUNCHER"
fi
# v0.1 put a symlink in /usr/local/bin. It points at the old folder, so it is dead now.
if [ -L "$OLD_LINK" ] && [[ "$(readlink "$OLD_LINK")" == "$OLD_DIR"/* ]]; then
    say "Removing old v0.1 link $OLD_LINK (needs sudo)"
    sudo rm -f "$OLD_LINK"
fi
if [ -d "$OLD_DIR/.git" ]; then
    say "Removing old install folder $OLD_DIR"
    rm -rf "$OLD_DIR"
fi

ok "sxmply installed."
case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *) warn "$BIN_DIR is not in your PATH. Add this to ~/.bashrc or ~/.zshrc, then open a new terminal:"
       echo "    export PATH=\"\$HOME/.local/bin:\$PATH\"" ;;
esac
echo "Try it:  sxmply clip --help     sxmply music --help"
echo "Update:  re-run ./install.sh     Remove:  ./install.sh --uninstall"
