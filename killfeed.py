from ursina import *

class KillFeed:
    def __init__(self, max_entries=4):
        self.max_entries = max_entries
        self._entries = []

    def add(self, killer_name, victim_name):
        if len(self._entries) >= self.max_entries:
            old = self._entries.pop(0)
            destroy(old)

        entry = Text(
            text=f'  {killer_name}  >  {victim_name}  ',
            position=window.top_right + Vec2(-0.01, -0.08 - len(self._entries) * 0.065),
            origin=(1, 0.5),
            scale=1.05,
            color=color.white,
            background=True,
        )
        self._entries.append(entry)
        invoke(self._expire, entry, delay=4)

    def _expire(self, entry):
        if entry in self._entries:
            self._entries.remove(entry)
        destroy(entry)


kill_feed = KillFeed()
