from player import Player
from config import SPAWN_POINTS, TEAM_COLORS, BLUE_NAMES, RED_NAMES


class Team:
    def __init__(self, name, color, spawn_points, names):
        self.name = name
        self.color = color
        self.spawn_points = spawn_points
        self.names = names
        self.players = []


class TeamManager:
    def __init__(self):
        # Use classic Counter‑Strike style names for the teams.  Internally we
        # still refer to them as "blue" and "red" via their colours, but the
        # human‑readable names now map to "Counter‑Terrorists" and "Terrorists".
        self.blue_team = Team('Counter-Terrorists', TEAM_COLORS['blue'], SPAWN_POINTS['blue'], BLUE_NAMES)
        self.red_team = Team('Terrorists', TEAM_COLORS['red'], SPAWN_POINTS['red'], RED_NAMES)

    def spawn_teams(self):
        for i in range(5):
            spawn = self.blue_team.spawn_points[i % len(self.blue_team.spawn_points)]
            name = self.blue_team.names[i % len(self.blue_team.names)]
            is_local = (i == 0)  # First player is local
            player = Player(team_color=self.blue_team.color, spawn_point=spawn, name=name, is_local=is_local, team_manager=self)
            self.blue_team.players.append(player)

        for i in range(5):
            spawn = self.red_team.spawn_points[i % len(self.red_team.spawn_points)]
            name = self.red_team.names[i % len(self.red_team.names)]
            player = Player(team_color=self.red_team.color, spawn_point=spawn, name=name, is_local=False, team_manager=self)
            self.red_team.players.append(player)

    def get_opposing_team(self, team_color):
        return self.red_team if team_color == self.blue_team.color else self.blue_team

    def get_opposing_players(self, team_color):
        return self.get_opposing_team(team_color).players

    @property
    def all_players(self):
        return self.blue_team.players + self.red_team.players


# Singleton instance
team_manager = TeamManager()
