from ursina import invoke

class SearchAndDestroyGameMode:
    """Simple search and destroy style mode.

    All players spawn at the start of a round and remain dead until the
    next round begins. A team wins the round when all opposing players
    are eliminated. After a short delay a new round starts and everyone
    respawns.
    """

    def __init__(self, team_manager):
        self.team_manager = team_manager
        self.team_manager.game_mode = self
        self.round_wins = {"blue": 0, "red": 0}
        self.round = 0
        self.round_active = False
        self.start_round()

    def start_round(self):
        self.round += 1
        for player in self.team_manager.all_players:
            player.respawn()
        self.round_active = True

    def player_died(self, player):
        # Called by TeamManager when a player dies.
        self.check_round_end()

    def check_round_end(self):
        blue_alive = any(not p.dead for p in self.team_manager.blue_team.players)
        red_alive = any(not p.dead for p in self.team_manager.red_team.players)
        if not blue_alive or not red_alive:
            winner = "red" if not blue_alive else "blue"
            self.round_wins[winner] += 1
            self.round_active = False
            invoke(self.start_round, delay=3)

    def update(self):
        # Currently all logic happens on death events but this method is
        # kept for potential future features.
        pass
