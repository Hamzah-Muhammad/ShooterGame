from ursina import *

class KillFeed:
    def __init__(self, max_entries=4):
        self.max_entries = max_entries
        self._entries = []

    def add(self, killer_name, victim_name, headshot=False):
        if len(self._entries) >= self.max_entries:
            old = self._entries.pop(0)
            destroy(old)

        arrow = ' >HS> ' if headshot else '  >  '
        entry = Text(
            text=f'  {killer_name}{arrow}{victim_name}  ',
            position=self._slot_position(len(self._entries)),
            origin=(1, 0.5),
            scale=1.05,
            color=color.yellow if headshot else color.white,
            background=True,
        )
        self._entries.append(entry)
        invoke(self._expire, entry, delay=4)

    def _slot_position(self, index):
        return window.top_right + Vec2(-0.01, -0.08 - index * 0.065)

    def _reposition(self):
        for i, entry in enumerate(self._entries):
            entry.position = self._slot_position(i)

    def _expire(self, entry):
        if entry in self._entries:
            self._entries.remove(entry)
        destroy(entry)
        self._reposition()


kill_feed = KillFeed()
