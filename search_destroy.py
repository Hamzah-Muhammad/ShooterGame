from ursina import Entity, Text, Button, Panel, color, destroy, time, distance, camera, application, mouse, invoke, Vec3
import math
import random
from config import (
    ROUND_LIMIT,
    BOMB_SITES,
    BOMB_TIMER,
    BOMB_PICKUP_RADIUS,
    BOMB_PLANT_RADIUS,
    BOMB_DEFUSE_RADIUS,
)

SITE_COLORS = [
    color.rgb(100, 255, 100),   # A - green
    color.rgb(255, 180, 180),   # B - pink
    color.rgb(100, 180, 255),   # C - blue
]
SITE_LABELS = ['A', 'B', 'C']


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

        # One marker entity per bomb site — all three are live plant targets
        self.plant_sites = []
        for i, site in enumerate(BOMB_SITES):
            marker = Entity(
                model='cube',
                color=SITE_COLORS[i],
                scale=3,
                position=site,
            )
            Entity(
                model='cube',
                color=color.rgba(255, 0, 0, 80),
                scale=6,
                position=(site[0], 0.05, site[2]),
            )
            Text(
                text=SITE_LABELS[i],
                position=(site[0], site[1] + 4, site[2]),
                scale=15,
                color=color.white,
                origin=(0, 0),
                world=True,
            )
            self.plant_sites.append(marker)

        # Red team starts as attackers
        self.attacking_team = self.team_manager.red_team
        self.defending_team = self.team_manager.blue_team
        self.rounds_played = 0
        self.switch_message = None
        self.win_screen = None
        self.bomb_timer_ui = None
        self.bomb_plant_notif = None

        # Countdown state for round start
        self.countdown_active = False
        self.countdown = 0
        self.countdown_text = None

        self.apply_team_colors()

    def start_round(self):
        """Respawn all players and reset bomb state."""
        for player in self.team_manager.all_players:
            player.respawn()

        if self.bomb_entity:
            destroy(self.bomb_entity)
        if self.planted_bomb:
            destroy(self.planted_bomb)
        if self.bomb_timer_ui:
            destroy(self.bomb_timer_ui)
            self.bomb_timer_ui = None
        if self.bomb_plant_notif:
            destroy(self.bomb_plant_notif)
            self.bomb_plant_notif = None

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

        self.apply_team_colors()
        self.start_countdown()

    def on_player_death(self, player):
        """Check if a team has been eliminated after a death."""
        team = (
            self.team_manager.blue_team
            if player.team_color == self.team_manager.blue_team.color
            else self.team_manager.red_team
        )
        remaining = [p for p in team.players if not p.dead]
        if self.bomb_carrier == player and not self.bomb_planted:
            self.drop_bomb(player.position)
        if not remaining:
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

        self.apply_team_colors()

        if self.blue_rounds >= self.round_limit:
            self._show_match_over('Blue Team')
        elif self.red_rounds >= self.round_limit:
            self._show_match_over('Red Team')
        else:
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
            if self.bomb_timer_ui:
                remaining = max(0, math.ceil(self.bomb_timer))
                self.bomb_timer_ui.text = f'BOMB  {remaining}s'
                if self.bomb_timer > 10:
                    self.bomb_timer_ui.color = color.red
                    self.bomb_timer_ui.enabled = True
                elif self.bomb_timer > 5:
                    self.bomb_timer_ui.color = color.orange
                    self.bomb_timer_ui.enabled = True
                else:
                    self.bomb_timer_ui.color = color.yellow
                    self.bomb_timer_ui.enabled = int(self.bomb_timer * 4) % 2 == 0
            if self.bomb_timer <= 0:
                self._explode_bomb()
                self._award_round(self.planting_team)

    def handle_action(self, player):
        """Attempt to plant or defuse the bomb."""
        if player.dead:
            return

        # Plant: carrier near any site
        if (
            player == self.bomb_carrier
            and not self.bomb_planted
            and player.team_color == self.attacking_team.color
        ):
            for site in self.plant_sites:
                if distance(player.position, site.position) < BOMB_PLANT_RADIUS:
                    self.plant_bomb(player, site.position)
                    return

        # Defuse: defender near planted bomb
        if (
            self.bomb_planted
            and self.planted_bomb
            and distance(player.position, self.planted_bomb.position) < BOMB_DEFUSE_RADIUS
            and player.team_color != self.planting_team.color
        ):
            self.defuse_bomb(player)

    def plant_bomb(self, player, position):
        self.planted_bomb = Entity(
            model='cube', color=color.black, scale=0.5, position=position
        )
        self.bomb_planted = True
        self.planting_team = self.attacking_team
        self.bomb_timer = BOMB_TIMER
        self.bomb_carrier = None
        player.has_bomb = False

        # "BOMB PLANTED" on-screen notification
        if self.bomb_plant_notif:
            destroy(self.bomb_plant_notif)
        self.bomb_plant_notif = Text(
            text='BOMB PLANTED',
            origin=(0, 0),
            scale=3,
            background=True,
            color=color.red,
        )
        destroy(self.bomb_plant_notif, delay=2)

        # Persistent bomb countdown HUD
        if self.bomb_timer_ui:
            destroy(self.bomb_timer_ui)
        self.bomb_timer_ui = Text(
            text=f'BOMB  {BOMB_TIMER}s',
            position=(0, -0.38),
            origin=(0, 0),
            scale=2,
            background=True,
            color=color.red,
        )

    def defuse_bomb(self, player):
        destroy(self.planted_bomb)
        self.planted_bomb = None
        self.bomb_planted = False
        if self.bomb_timer_ui:
            destroy(self.bomb_timer_ui)
            self.bomb_timer_ui = None
        self._award_round(self.team_manager.get_opposing_team(self.planting_team.color))

    def drop_bomb(self, position):
        if self.bomb_entity or self.bomb_planted:
            return
        self.bomb_entity = Entity(
            model='cube', color=color.black, scale=0.5, position=position
        )
        self.bomb_carrier = None

    def apply_team_colors(self):
        """Color attacking team red and defenders blue."""
        self.attacking_team.color = color.red
        self.defending_team.color = color.azure
        for p in self.attacking_team.players:
            p.color = color.red
            p.team_color = color.red
        for p in self.defending_team.players:
            p.color = color.azure
            p.team_color = color.azure

    def show_switch_message(self):
        if self.switch_message:
            destroy(self.switch_message)
        self.switch_message = Text(
            text='Sides switched!',
            origin=(0, 0),
            scale=2,
            background=True,
            color=color.white,
        )
        destroy(self.switch_message, delay=3)

    def start_countdown(self, seconds: int = 3):
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

    def _explode_bomb(self):
        if not self.planted_bomb:
            return
        pos = Vec3(self.planted_bomb.position)

        blast_colors = [color.orange, color.yellow, color.rgb(255, 80, 0)]
        for i in range(20):
            p = Entity(
                model='sphere',
                color=blast_colors[i % 3],
                scale=random.uniform(0.5, 2.5),
                position=pos + Vec3(
                    random.uniform(-5, 5),
                    random.uniform(0, 8),
                    random.uniform(-5, 5),
                ),
            )
            p.animate_scale(0, duration=random.uniform(0.4, 1.2))
            destroy(p, delay=1.2)

        shockwave = Entity(
            model='sphere',
            color=color.rgba(255, 160, 50, 160),
            scale=1,
            position=pos,
        )
        shockwave.animate_scale(35, duration=0.7)
        destroy(shockwave, delay=0.7)

        if self.bomb_timer_ui:
            destroy(self.bomb_timer_ui)
            self.bomb_timer_ui = None

    def _show_match_over(self, winner_name):
        application.paused = True
        mouse.locked = False

        self.win_screen = Entity(parent=camera.ui, ignore_paused=True)
        Panel(
            parent=self.win_screen,
            scale=(0.55, 0.4),
            color=color.rgba(0, 0, 0, 200),
            ignore_paused=True,
        )
        Text(
            text=f'{winner_name} wins the match!',
            parent=self.win_screen,
            position=(0, 0.12),
            origin=(0, 0),
            scale=2,
            color=color.white,
            ignore_paused=True,
        )
        Text(
            text=f'Blue: {self.blue_rounds}  |  Red: {self.red_rounds}',
            parent=self.win_screen,
            position=(0, 0.04),
            origin=(0, 0),
            scale=1.2,
            color=color.light_gray,
            ignore_paused=True,
        )
        Button(
            text='Play Again',
            parent=self.win_screen,
            position=(0, -0.06),
            scale=(0.25, 0.06),
            on_click=self._restart_match,
            ignore_paused=True,
        )
        Button(
            text='Quit',
            parent=self.win_screen,
            position=(0, -0.15),
            scale=(0.25, 0.06),
            on_click=application.quit,
            ignore_paused=True,
        )

    def _restart_match(self):
        if self.win_screen:
            destroy(self.win_screen)
            self.win_screen = None
        self.blue_rounds = 0
        self.red_rounds = 0
        self.rounds_played = 0
        application.paused = False
        mouse.locked = True
        self.start_round()


# Global instance used throughout the game
sd_game = None
