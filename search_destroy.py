from ursina import Entity, Text, color, destroy, time, distance
import math
from config import (
    ROUND_LIMIT,
    BOMB_SPAWN,
    BOMB_SITE_B,
    BOMB_TIMER,
    BOMB_PICKUP_RADIUS,
    BOMB_PLANT_RADIUS,
    BOMB_DEFUSE_RADIUS,
)


class SearchAndDestroyGame:
    """Manage Search & Destroy rounds and scores."""
    def __init__(self, team_manager):
        self.team_manager = team_manager
        self.round_limit = ROUND_LIMIT
        self.blue_rounds = 0
        self.red_rounds = 0

        self.bomb_entity = None
        self.planted_bomb = None
        self.bomb_carrier = None
        self.planting_team = None
        self.bomb_timer = 0
        self.bomb_planted = False

        # Only site B is used for planting. Make it highly visible
        self.plant_site = Entity(
            model='cube',
            color=color.rgb(255, 180, 180),
            scale=3,
            position=BOMB_SITE_B,
        )
        # Large translucent box to highlight the site
        self.plant_highlight = Entity(
            model='cube',
            color=color.rgba(255, 0, 0, 80),
            scale=6,
            position=(BOMB_SITE_B[0], 0.05, BOMB_SITE_B[2]),
        )

        # The red team starts as the attackers
        self.attacking_team = self.team_manager.red_team
        self.defending_team = self.team_manager.blue_team
        self.rounds_played = 0
        self.switch_message = None

        # Countdown state for round start
        self.countdown_active = False
        self.countdown = 0
        self.countdown_text = None

        # Ensure player colours match the current roles
        self.apply_team_colors()

    def start_round(self):
        """Respawn all players and reset bomb state."""
        for player in self.team_manager.all_players:
            player.respawn()

        if self.bomb_entity:
            destroy(self.bomb_entity)
        if self.planted_bomb:
            destroy(self.planted_bomb)

        # Spawn the bomb near the attacking team's spawn
        spawn_point = self.attacking_team.spawn_points[0]
        spawn_pos = (spawn_point[0], 1, spawn_point[2])
        self.bomb_entity = Entity(
            model='cube', color=color.black, scale=0.5, position=spawn_pos
        )
        self.planted_bomb = None
        self.bomb_carrier = None
        self.planting_team = None
        self.bomb_timer = 0
        self.bomb_planted = False

        # Update player colours for the current roles
        self.apply_team_colors()

        # Begin round countdown
        self.start_countdown()

    def on_player_death(self, player):
        """Check if a team has been eliminated after a death."""
        team = self.team_manager.blue_team if player.team_color == self.team_manager.blue_team.color else self.team_manager.red_team
        remaining = [p for p in team.players if not p.dead]
        if self.bomb_carrier == player and not self.bomb_planted:
            self.drop_bomb(player.position)
        if not remaining:
            # Opposing team wins the round
            winner = self.team_manager.get_opposing_team(player.team_color)
            self._award_round(winner)

    def _award_round(self, team):
        if team == self.team_manager.blue_team:
            self.blue_rounds += 1
        else:
            self.red_rounds += 1

        self.rounds_played += 1
        if self.rounds_played % 2 == 0:
            self.attacking_team, self.defending_team = (
                self.defending_team,
                self.attacking_team,
            )
            self.show_switch_message()

        # Update colours whenever roles may have changed
        self.apply_team_colors()

        if self.blue_rounds >= self.round_limit or self.red_rounds >= self.round_limit:
            # Match over, reset scores
            self.blue_rounds = 0
            self.red_rounds = 0

        self.start_round()

    def update(self):
        """Update bomb logic each frame."""
        if self.countdown_active:
            self.countdown -= time.dt
            remaining = math.ceil(self.countdown)
            if remaining > 0:
                self.countdown_text.text = str(remaining)
            if self.countdown <= 0:
                self.countdown_active = False
                destroy(self.countdown_text)
                self.countdown_text = None
            return

        if not self.bomb_planted and not self.bomb_carrier and self.bomb_entity:
            for p in self.attacking_team.players:
                if p.dead:
                    continue
                if distance(p.position, self.bomb_entity.position) < BOMB_PICKUP_RADIUS:
                    self.bomb_carrier = p
                    p.has_bomb = True
                    destroy(self.bomb_entity)
                    self.bomb_entity = None
                    break

        if self.bomb_planted:
            self.bomb_timer -= time.dt
            if self.bomb_timer <= 0:
                self._award_round(self.planting_team)

    def handle_action(self, player):
        """Attempt to plant or defuse the bomb."""
        if player.dead:
            return
        if (
            player == self.bomb_carrier
            and not self.bomb_planted
            and player.team_color == self.attacking_team.color
            and distance(player.position, self.plant_site.position)
            < BOMB_PLANT_RADIUS
        ):
            self.plant_bomb(player)
        elif (
            self.bomb_planted
            and distance(player.position, self.planted_bomb.position)
            < BOMB_DEFUSE_RADIUS
            and player.team_color != self.planting_team.color
        ):
            self.defuse_bomb(player)

    def plant_bomb(self, player):
        self.planted_bomb = Entity(
            model='cube', color=color.black, scale=0.5, position=self.plant_site.position
        )
        self.bomb_planted = True
        self.planting_team = self.attacking_team
        self.bomb_timer = BOMB_TIMER
        self.bomb_carrier = None
        player.has_bomb = False

    def defuse_bomb(self, player):
        destroy(self.planted_bomb)
        self.planted_bomb = None
        self.bomb_planted = False
        self._award_round(self.team_manager.get_opposing_team(self.planting_team.color))

    def drop_bomb(self, position):
        if self.bomb_entity or self.bomb_planted:
            return
        self.bomb_entity = Entity(model='cube', color=color.black, scale=0.5, position=position)
        self.bomb_carrier = None

    def apply_team_colors(self):
        """Color attacking team red and defenders blue."""
        # Update the team objects' colour attributes so helper methods that rely
        # on these values (like TeamManager.get_opposing_team) continue to work
        # after sides switch.
        self.attacking_team.color = color.red
        self.defending_team.color = color.azure
        for p in self.attacking_team.players:
            p.color = color.red
            p.team_color = color.red
        for p in self.defending_team.players:
            p.color = color.azure
            p.team_color = color.azure

    def show_switch_message(self):
        """Display a temporary message when teams switch roles."""
        if self.switch_message:
            destroy(self.switch_message)
        self.switch_message = Text(
            text="Sides switched!",
            origin=(0, 0),
            scale=2,
            background=True,
            color=color.white,
        )
        destroy(self.switch_message, delay=3)

    def start_countdown(self, seconds: int = 3):
        """Display a countdown before the round starts."""
        if self.countdown_text:
            destroy(self.countdown_text)
        self.countdown = seconds
        self.countdown_active = True
        self.countdown_text = Text(
            text=str(seconds),
            origin=(0, 0),
            scale=4,
            background=True,
            color=color.white,
        )



# Global instance used throughout the game
sd_game = None
