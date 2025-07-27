from ursina import Entity, color, destroy, time, distance
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

        # Only site B is used for planting
        self.plant_site = Entity(
            model='cube', color=color.orange, scale=3, position=BOMB_SITE_B
        )

        self.attacking_team = self.team_manager.blue_team
        self.defending_team = self.team_manager.red_team
        self.rounds_played = 0

    def start_round(self):
        """Respawn all players and reset bomb state."""
        for player in self.team_manager.all_players:
            player.respawn()

        if self.bomb_entity:
            destroy(self.bomb_entity)
        if self.planted_bomb:
            destroy(self.planted_bomb)

        self.bomb_entity = Entity(model='sphere', color=color.white, scale=1,
                                 position=BOMB_SPAWN)
        self.planted_bomb = None
        self.bomb_carrier = None
        self.planting_team = None
        self.bomb_timer = 0
        self.bomb_planted = False

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

        if self.blue_rounds >= self.round_limit or self.red_rounds >= self.round_limit:
            # Match over, reset scores
            self.blue_rounds = 0
            self.red_rounds = 0

        self.start_round()

    def update(self):
        """Update bomb logic each frame."""
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
            model='sphere', color=color.red, scale=1, position=self.plant_site.position
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
        self.bomb_entity = Entity(model='sphere', color=color.white, scale=1, position=position)
        self.bomb_carrier = None


# Global instance used throughout the game
sd_game = None
