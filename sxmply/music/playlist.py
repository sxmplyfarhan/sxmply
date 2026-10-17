                                                               
import random

REPEAT_MODES = ("off", "all", "one")


class Queue:
    def __init__(self):
        self.tracks = []
        self.order = []                                                         
        self.pos = -1                            
        self.shuffle = False
        self.repeat = "off"

    def set_tracks(self, tracks, start=0):
        self.tracks = list(tracks)
        self._build(start if self.tracks else None)

    def _build(self, first):
        n = len(self.tracks)
        if n == 0:
            self.order, self.pos = [], -1
            return
        if first is None or not 0 <= first < n:
            first = 0
        if self.shuffle:                                                              
            rest = [i for i in range(n) if i != first]
            random.shuffle(rest)
            self.order, self.pos = [first] + rest, 0
        else:
            self.order, self.pos = list(range(n)), first

    @property
    def current(self):
        if 0 <= self.pos < len(self.order):
            return self.tracks[self.order[self.pos]]
        return None

    def set_shuffle(self, on):
        cur = self.order[self.pos] if 0 <= self.pos < len(self.order) else None
        self.shuffle = on
        if self.tracks:
            self._build(cur)                                                       

    def cycle_repeat(self):
        self.repeat = REPEAT_MODES[(REPEAT_MODES.index(self.repeat) + 1) % len(REPEAT_MODES)]
        return self.repeat

    def advance(self, auto=False):
\
                                                                                              
        if not self.order:
            return None
        if auto and self.repeat == "one":
            return self.current
        if self.pos + 1 < len(self.order):
            self.pos += 1
        else:
            if auto and self.repeat == "off":
                return None
            self._wrap()
        return self.current

    def _wrap(self):
        if self.shuffle:
            last = self.order[self.pos] if 0 <= self.pos < len(self.order) else None
            order = list(range(len(self.order)))
            random.shuffle(order)
            if len(order) > 1 and order[0] == last:                                           
                order[0], order[1] = order[1], order[0]
            self.order = order
        self.pos = 0

    def previous(self):
        if not self.order:
            return None
        self.pos = self.pos - 1 if self.pos > 0 else len(self.order) - 1
        return self.current
