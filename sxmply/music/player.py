   
import json
import os
import queue
import shutil
import socket
import subprocess
import tempfile
import threading
import time


class PlayerError(Exception):
    pass


class MpvPlayer:
    def __init__(self, volume=70):
        self.volume = int(volume)
        self.position = 0.0
        self.duration = 0.0
        self.paused = False
        self.muted = False
        self.speed = 1.0
        self.video_on = False                                                            
        self.events = queue.Queue()                                                
        self._proc = None
        self._sock = None
        self._sock_path = None
        self._lock = threading.Lock()

                                        
    def start(self):
        exe = shutil.which("mpv")
        if not exe:
            raise PlayerError(
                "mpv is not installed. It is the engine that plays the sound.\n"
                "  Debian/Ubuntu: sudo apt install mpv     Fedora: sudo dnf install mpv\n"
                "  Arch: sudo pacman -S mpv                macOS: brew install mpv")
        tmp = "/tmp" if os.path.isdir("/tmp") else tempfile.gettempdir()                                                
        self._sock_path = os.path.join(tmp, f"sxmply-mpv-{os.getpid()}.sock")
        try:
            os.unlink(self._sock_path)
        except OSError:
            pass
        self._proc = subprocess.Popen(
            [exe, "--idle=yes", "--no-video", "--no-terminal", "--force-window=no",
             "--audio-display=no", f"--volume={self.volume}",
             f"--input-ipc-server={self._sock_path}"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        deadline = time.monotonic() + 5
        while True:
            if self._proc.poll() is not None:
                raise PlayerError("mpv stopped right after starting. Run 'mpv --version' to check it works.")
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.connect(self._sock_path)
                self._sock = s
                break
            except OSError:
                s.close()
                if time.monotonic() > deadline:
                    self.close()
                    raise PlayerError("couldn't connect to mpv.")
                time.sleep(0.05)

        threading.Thread(target=self._listen, daemon=True).start()
                                                     
        for i, prop in enumerate(("time-pos", "duration", "pause", "volume", "mute", "speed"), 1):
            self._send("observe_property", i, prop)

    def close(self):
        self._send("quit")
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
        if self._proc:
            try:
                self._proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        if self._sock_path:
            try:
                os.unlink(self._sock_path)
            except OSError:
                pass

                                          
    def _send(self, *command):
        if not self._sock:
            return
        data = (json.dumps({"command": list(command)}) + "\n").encode()
        with self._lock:
            try:
                self._sock.sendall(data)
            except OSError:
                pass

    def _listen(self):
        buf = b""
        while True:
            try:
                chunk = self._sock.recv(65536)
            except OSError:
                break
            if not chunk:
                break
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                try:
                    self._handle(json.loads(line))
                except ValueError:
                    continue
        self.events.put(("closed",))

    def _handle(self, msg):
        event = msg.get("event")
        if event == "property-change":
            name, data = msg.get("name"), msg.get("data")
            if name == "time-pos":
                self.position = float(data or 0)
            elif name == "duration":
                self.duration = float(data or 0)
            elif name == "pause":
                self.paused = bool(data)
            elif name == "volume" and data is not None:
                self.volume = int(round(data))
            elif name == "mute":
                self.muted = bool(data)
            elif name == "speed" and data is not None:
                self.speed = float(data)
        elif event == "file-loaded":
            self.events.put(("loaded",))
        elif event == "end-file":
            reason = msg.get("reason")
            if reason in ("eof", "error"):                                    
                self.events.put(("end", reason))

                                    
    def load(self, path):
        self.position = 0.0
        self.duration = 0.0
        self.paused = False
        self._send("loadfile", path, "replace")
        self._send("set_property", "pause", False)

    def toggle_pause(self):
        self.paused = not self.paused
        self._send("cycle", "pause")

    def seek(self, seconds, mode="relative"):
        self._send("seek", seconds, mode)

    def set_volume(self, value):
        self.volume = max(0, min(100, int(value)))
        self._send("set_property", "volume", self.volume)

    def toggle_mute(self):
        self.muted = not self.muted
        self._send("cycle", "mute")

    def set_speed(self, value):
        self.speed = round(max(0.5, min(2.0, value)), 2)
        self._send("set_property", "speed", self.speed)

    def set_video(self, on):

                                                                                               
        self.video_on = bool(on)
        self._send("set_property", "vid", "auto" if on else "no")

    def pause(self):
        if not self.paused:
            self.toggle_pause()

    def stop(self):
        self.position = 0.0
        self.duration = 0.0
        self._send("stop")
