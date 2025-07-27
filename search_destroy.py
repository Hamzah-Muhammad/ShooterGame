from config import ROUND_LIMIT


class SearchAndDestroyGame:
    """Manage Search & Destroy rounds and scores."""
    def __init__(self, team_manager):
        self.team_manager = team_manager
        self.round_limit = ROUND_LIMIT
        self.blue_rounds = 0
        self.red_rounds = 0

    def start_round(self):
        """Respawn all players at their spawn points."""
        for player in self.team_manager.all_players:
            player.respawn()

    def on_player_death(self, player):
        """Check if a team has been eliminated after a death."""
        team = self.team_manager.blue_team if player.team_color == self.team_manager.blue_team.color else self.team_manager.red_team
        remaining = [p for p in team.players if not p.dead]
        if not remaining:
            # Opposing team wins the round
            winner = self.team_manager.get_opposing_team(player.team_color)
            self._award_round(winner)

    def _award_round(self, team):
        if team == self.team_manager.blue_team:
            self.blue_rounds += 1
        else:
            self.red_rounds += 1

        if self.blue_rounds >= self.round_limit or self.red_rounds >= self.round_limit:
            # Match over, reset scores
            self.blue_rounds = 0
            self.red_rounds = 0

        self.start_round()


# Global instance used throughout the game
sd_game = None
