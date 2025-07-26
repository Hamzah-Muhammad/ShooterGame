# scoreboard.py - Tracks kills, deaths, and displays score UI

from ursina import *
from constants import MAX_SCORE

class Scoreboard:
    def __init__(self):
        self.kills = {'blue': 0, 'red': 0}
        self.ui = Text('', origin=(0, 0.5), position=(-0.8, 0.45), scale=1.5)

    def add_kill(self, killer_team):
        self.kills[killer_team] += 1
        self.update_ui()

    def update_ui(self):
        self.ui.text = f"Blue: {self.kills['blue']}  |  Red: {self.kills['red']}"

    def check_victory(self):
        for team, score in self.kills.items():
            if score >= MAX_SCORE:
                self.ui.text = f"{team.upper()} TEAM WINS!"
                application.pause()