\
\
\
\
   
import os
import re
import sys


def _color_enabled():
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty() and os.environ.get("TERM") != "dumb"


USE_COLOR = _color_enabled()
CLEAR_LINE = "\033[K" if USE_COLOR else ""

_CODES = {
    "bold": "1", "dim": "2", "reverse": "7",
    "red": "31", "green": "32", "yellow": "33",
    "blue": "34", "magenta": "35", "cyan": "36", "gray": "90",
}


def paint(text, *styles):
    if not USE_COLOR:
        return str(text)
    codes = ";".join(_CODES[s] for s in styles)
    return f"\033[{codes}m{text}\033[0m"


                        
def info(msg):
    print(f"{paint('›', 'cyan', 'bold')} {msg}")


def success(msg):
    print(f"{paint('✔', 'green', 'bold')} {msg}")


def warn(msg):
    print(f"{paint('!', 'yellow', 'bold')} {msg}")


def error(msg):
    print(f"{paint('✘', 'red', 'bold')} {msg}", file=sys.stderr)


def heading(msg):
    print(f"\n{paint(msg, 'magenta', 'bold')}")


def banner(tool="", tagline=""):
    if not sys.stdout.isatty():
        return
    line = paint("♪ sxmply", "magenta", "bold")
    if tool:
        line += " " + paint(tool, "cyan", "bold")
    if tagline:
        line += paint("  " + tagline, "gray")
    print(line)


                       
def ask(question):
                                                                                         
    text = f"{paint('?', 'magenta', 'bold')} {question} {paint('›', 'gray')} "
    if USE_COLOR:
        text = re.sub(r"(\x1b\[[0-9;]*m)", "\001\\1\002", text)
    return input(text).strip()


def choose_count(total, noun="items"):
                                                                             
    while True:
        choice = ask(f"How many {noun}? (1-{total}, or 'a' for all)").lower()
        if choice == "a":
            return total
        if choice.isdigit() and 1 <= int(choice) <= total:
            return int(choice)
        warn(f"Enter a number between 1 and {total}, or 'a' for all.")


def menu(question, options, default=0):
                                                                                  
    print(f"\n{paint(question, 'bold')}")
    for i, label in enumerate(options, 1):
        tag = paint("  (default)", "gray") if i - 1 == default else ""
        print(f"  {paint(i, 'cyan')}. {label}{tag}")
    while True:
        choice = ask(f"Choose 1-{len(options)} (Enter = {default + 1})")
        if not choice:
            return default
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return int(choice) - 1
        warn(f"Enter a number between 1 and {len(options)}, or just press Enter.")


def ask_default(question, default):
                                                         
    answer = ask(f"{question} [{default}]")
    return answer or default


def preview(titles, total):
    for i, title in enumerate(titles, 1):
        print(f"  {paint(i, 'cyan')}. {title}")
    if total > len(titles):
        print(paint(f"  … and {total - len(titles)} more", "gray"))


                                           
BAR_LEN = 30


def _fmt_bytes(n):
    for unit in ("B", "KiB", "MiB", "GiB"):
        if n < 1024 or unit == "GiB":
            return f"{n:.1f}{unit}" if unit != "B" else f"{int(n)}B"
        n /= 1024


def _bar(fraction):
    filled = int(BAR_LEN * fraction)
    return paint("█" * filled, "green") + paint("░" * (BAR_LEN - filled), "gray")


def progress_hook(d):
    status = d.get("status")
    if status == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        done = d.get("downloaded_bytes") or 0
        fraction = min(done / total, 1.0) if total else 0.0
        speed = d.get("speed")
        eta = d.get("eta")
        speed_s = f"{_fmt_bytes(speed)}/s" if speed else "--"
        eta_s = f"ETA {int(eta)}s" if eta is not None else ""
        sys.stdout.write(
            f"\r{CLEAR_LINE}{_bar(fraction)} {fraction * 100:5.1f}%  "
            f"{paint(speed_s, 'cyan')}  {paint(eta_s, 'gray')}"
        )
        sys.stdout.flush()
    elif status == "finished":
        sys.stdout.write(f"\r{CLEAR_LINE}{_bar(1.0)} 100.0%\n")
        sys.stdout.flush()


def postprocess_hook(d):
    if d.get("status") == "started":
        sys.stdout.write(f"\r{CLEAR_LINE}{paint('Converting…', 'dim')}")
        sys.stdout.flush()
    elif d.get("status") == "finished":
        sys.stdout.write(f"\r{CLEAR_LINE}")
        sys.stdout.flush()
