                                                                     
import os
import select
import sys
import termios
import tty

_CSI = {
    "A": "up", "B": "down", "C": "right", "D": "left", "H": "home", "F": "end",
    "1~": "home", "4~": "end", "5~": "pgup", "6~": "pgdn", "3~": "delete",
    "1;2C": "S-right", "1;2D": "S-left", "1;2A": "S-up", "1;2B": "S-down",
}


class Keys:
                                                                              

    def __enter__(self):
        self.fd = sys.stdin.fileno()
        self._old = termios.tcgetattr(self.fd)
        tty.setcbreak(self.fd)
        return self

    def __exit__(self, *exc):
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self._old)

    def suspend(self):
                                                                                         
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self._old)

    def resume(self):
        tty.setcbreak(self.fd)
        termios.tcflush(self.fd, termios.TCIFLUSH)                                       

    def _byte(self, timeout):
        if not select.select([self.fd], [], [], timeout)[0]:
            return None
        return os.read(self.fd, 1)

    def read(self, timeout=0.2):
        b = self._byte(timeout)
        if b is None:
            return None
        if b == b"\x1b":
            return self._escape()
        if b in (b"\n", b"\r"):
            return "enter"
        if b in (b"\x7f", b"\x08"):
            return "backspace"
        if b == b"\t":
            return "tab"
        c = b[0]
        if c < 0x20:
            return ""                              
        if c >= 0xC0:                                                     
            need = 1 if c < 0xE0 else 2 if c < 0xF0 else 3
            for _ in range(need):
                nxt = self._byte(0.05)
                if nxt is None:
                    break
                b += nxt
        return b.decode("utf-8", "replace")

    def _escape(self):
        b = self._byte(0.03)
        if b is None:
            return "esc"                              
        if b == b"[":
            seq = b""
            while True:
                nxt = self._byte(0.03)
                if nxt is None:
                    return ""
                seq += nxt
                if 0x40 <= nxt[0] <= 0x7E:                              
                    break
            return _CSI.get(seq.decode("ascii", "replace"), "")
        if b == b"O":                                                      
            nxt = self._byte(0.03)
            return _CSI.get(nxt.decode("ascii", "replace"), "") if nxt else ""
        return ""                                    
