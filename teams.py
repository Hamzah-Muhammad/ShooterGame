# teams.py - Manages team colors and spawn points

from constants import TEAM_COLORS, SPAWN_POINTS

class TeamManager:
    def __init__(self):
        self.teams = {
            'blue': [],
            'red': []
        }

    def assign_team(self, player, team_name):
        player.team = team_name
        player.color = TEAM_COLORS[team_name]
        self.teams[team_name].append(player)

    def get_spawn_points(self, team_name):
        return SPAWN_POINTS[team_name]