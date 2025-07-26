from ursina import *
from player import Player
from teams import TeamManager
from scoreboard import Scoreboard
from map import create_map
from constants import SPAWN_POINTS

app = Ursina()
create_map()

team_mgr = TeamManager()
scoreboard = Scoreboard()
players = []

def spawn_teams():
    for i in range(5):
        is_player = (i == 0)  # Only first blue is the local player

        blue = Player(
            team_color=color.azure,
            spawn_point=SPAWN_POINTS['blue'][i],
            is_local=is_player
        )
        red = Player(
            team_color=color.red,
            spawn_point=SPAWN_POINTS['red'][i],
            is_local=False
        )

        team_mgr.assign_team(blue, 'blue')
        team_mgr.assign_team(red, 'red')

        blue.scoreboard = scoreboard
        red.scoreboard = scoreboard

        players.append(blue)
        players.append(red)

def update():
    for p in players:
        p.update()

spawn_teams()
app.run()
