from ursina import Vec3
from player import Player
import random

class Team:
    def __init__(self, name, color, spawn_area=(0, 0, 0)):
        self.name = name
        self.color = color
        self.players = []
        self.spawn_area = spawn_area

    def add_player(self):
        spawn = Vec3(
            self.spawn_area[0] + random.uniform(-3, 3),
            self.spawn_area[1],
            self.spawn_area[2] + random.uniform(-3, 3)
        )
        p = Player(team_color=self.color, spawn_point=self.spawn_area)
        self.players.append(p)

