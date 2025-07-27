from ursina import *
import search_destroy

class Scoreboard(Entity):
    def __init__(self, team_manager):
        super().__init__()
        self.team_manager = team_manager

        self.blue_text = Text(
            text='Blue: 0',
            position=window.top_left + Vec2(0.05, -0.05),
            origin=(0, 0),
            scale=1.5,
            color=color.azure
        )
        self.red_text = Text(
            text='Red: 0',
            position=window.top_left + Vec2(0.05, -0.12),
            origin=(0, 0),
            scale=1.5,
            color=color.red
        )

    def update(self):
        self.update_score()

    def update_score(self):
        if search_destroy.sd_game:
            self.blue_text.text = f"Blue: {search_destroy.sd_game.blue_rounds}"
            self.red_text.text = f"Red: {search_destroy.sd_game.red_rounds}"
        else:
            blue_kills = sum([p.kills for p in self.team_manager.blue_team.players])
            red_kills = sum([p.kills for p in self.team_manager.red_team.players])
            self.blue_text.text = f'Blue: {blue_kills}'
            self.red_text.text = f'Red: {red_kills}'
