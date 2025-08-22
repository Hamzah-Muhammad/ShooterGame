from ursina import *
import search_destroy

class Scoreboard(Entity):
    def __init__(self, team_manager):
        """Display round or kill scores for both teams.

        The text labels pull their names from ``team_manager`` so that they read
        "Counter‑Terrorists" and "Terrorists" rather than the more generic
        "Team 1"/"Team 2".  This small tweak helps the demo feel closer to a
        traditional Counter‑Strike style scoreboard.
        """
        super().__init__()
        self.team_manager = team_manager

        # The colours of these labels will swap depending on which team is
        # currently attacking in Search & Destroy.
        self.team1_text = Text(
            text=f"{self.team_manager.blue_team.name}: 0",
            position=window.top_left + Vec2(0.05, -0.05),
            origin=(-0.5, 0.5),
            scale=1.25,
            color=color.azure,
        )
        self.team2_text = Text(
            text=f"{self.team_manager.red_team.name}: 0",
            position=window.top_left + Vec2(0.05, -0.12),
            origin=(-0.5, 0.5),
            scale=1.25,
            color=color.red,
        )

    def update(self):
        self.update_score()

    def update_score(self):
        if search_destroy.sd_game:
            team1_score = search_destroy.sd_game.blue_rounds
            team2_score = search_destroy.sd_game.red_rounds
        else:
            team1_score = sum(p.kills for p in self.team_manager.blue_team.players)
            team2_score = sum(p.kills for p in self.team_manager.red_team.players)

        self.team1_text.text = f'{self.team_manager.blue_team.name}: {team1_score}'
        self.team2_text.text = f'{self.team_manager.red_team.name}: {team2_score}'

        # Update colours based on the current attacking team
        if search_destroy.sd_game:
            if search_destroy.sd_game.attacking_team == self.team_manager.blue_team:
                self.team1_text.color = color.red
                self.team2_text.color = color.azure
            else:
                self.team1_text.color = color.azure
                self.team2_text.color = color.red
