from player import Player
from config import SPAWN_POINTS, TEAM_COLORS
import random

class Team:
    def __init__(self, color):
        self.color = color
        self.players = []

    def add_player(self, player):
        self.players.append(player)

    def remove_player(self, player):
        if player in self.players:
            self.players.remove(player)


class TeamManager:
    def __init__(self):
        self.blue_team = Team('blue')
        self.red_team = Team('red')
        self.blue_names = self._generate_names(5)
        self.red_names = self._generate_names(5)

    def spawn_teams(self):
        from ursina import scene  # Needed here to avoid circular import

        # Spawn 5 blue players
        for i in range(5):
            is_local = i == 0
            player = Player(
                team_color=TEAM_COLORS['blue'],
                spawn_point=SPAWN_POINTS['blue'][i],
                is_local=is_local,
                name=self.blue_names[i],
                team_manager=self
            )
            player.parent = scene
            self.blue_team.add_player(player)

        # Spawn 5 red players
        for i in range(5):
            player = Player(
                team_color=TEAM_COLORS['red'],
                spawn_point=SPAWN_POINTS['red'][i],
                is_local=False,
                name=self.red_names[i],
                team_manager=self
            )
            player.parent = scene
            self.red_team.add_player(player)

    def get_team(self, color):
        return self.blue_team if color == 'blue' else self.red_team

    def get_opposing_team(self, color):
        return self.red_team if color == 'blue' else self.blue_team

    def get_opposing_players(self, team_color):
        opposing_team = self.get_opposing_team(team_color)
        return opposing_team.players if opposing_team else []

    def _generate_names(self, count):
        names = [
            "Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Ghost",
            "Hunter", "Iceman", "Joker", "Knight", "Lion", "Maverick", "Nova",
            "Oscar", "Phoenix", "Ranger", "Shadow", "Titan", "Viper"
        ]
        return random.sample(names, count)


# Singleton instance
team_manager = TeamManager()
