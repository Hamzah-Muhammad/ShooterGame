from ursina import *
import search_destroy

class Scoreboard(Entity):
    def __init__(self, team_manager):
        super().__init__()
        self.team_manager = team_manager

        self.team1_text = Text(
            text='Blue: 0',
            position=window.top_left + Vec2(0.05, -0.05),
            origin=(-0.5, 0.5),
            scale=1.4,
            color=color.azure,
            background=True,
        )
        self.team2_text = Text(
            text='Red: 0',
            position=window.top_left + Vec2(0.05, -0.13),
            origin=(-0.5, 0.5),
            scale=1.4,
            color=color.red,
            background=True,
        )
        self.round_text = Text(
            text='',
            position=window.top + Vec2(0, -0.05),
            origin=(0, 0.5),
            scale=1.3,
            color=color.white,
            background=True,
        )

    def update(self):
        self.update_score()

    def update_score(self):
        if search_destroy.sd_game:
            blue_score = search_destroy.sd_game.blue_rounds
            red_score  = search_destroy.sd_game.red_rounds
            limit      = search_destroy.sd_game.round_limit
            round_num  = search_destroy.sd_game.rounds_played + 1
            self.round_text.text = f'Round {round_num}  |  First to {limit}'
        else:
            blue_score = sum(p.kills for p in self.team_manager.blue_team.players)
            red_score  = sum(p.kills for p in self.team_manager.red_team.players)
            self.round_text.text = ''

        self.team1_text.text = f'Blue  {blue_score}'
        self.team2_text.text = f'Red   {red_score}'

        # Attacking team label turns red (pressure indicator)
        if search_destroy.sd_game:
            if search_destroy.sd_game.attacking_team == self.team_manager.blue_team:
                self.team1_text.color = color.red
                self.team2_text.color = color.azure
            else:
                self.team1_text.color = color.azure
                self.team2_text.color = color.red
