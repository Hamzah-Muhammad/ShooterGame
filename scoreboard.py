from ursina import *
import search_destroy

class Scoreboard(Entity):
    def __init__(self, team_manager):
        super().__init__()
        self.team_manager = team_manager

        # "Team 1" corresponds to the blue team and "Team 2" to the red team.
        # The colours of these labels will swap depending on which team is
        # currently attacking in Search & Destroy.
        self.team1_text = Text(
            text='Team 1: 0',
            position=window.top_left + Vec2(0.05, -0.05),
            origin=(-0.5, 0.5),
            scale=1.25,
            color=color.azure,
        )
        self.team2_text = Text(
            text='Team 2: 0',
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

        self.team1_text.text = f'Team 1: {team1_score}'
        self.team2_text.text = f'Team 2: {team2_score}'

        # Update colours based on the current attacking team
        if search_destroy.sd_game:
            if search_destroy.sd_game.attacking_team == self.team_manager.blue_team:
                self.team1_text.color = color.red
                self.team2_text.color = color.azure
            else:
                self.team1_text.color = color.azure
                self.team2_text.color = color.red
