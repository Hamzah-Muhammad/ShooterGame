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
    BOMB_BLAST_RADIUS,
    BOMB_BLAST_DAMAGE,
    ROUND_TIME,
    PLANT_TIME,
    DEFUSE_TIME,
    ROUND_OVER_DURATION,
)

SITE_COLORS = [
    color.rgb32(100, 255, 100),   # A - green
    color.rgb32(255, 180, 180),   # B - pink
    color.rgb32(100, 180, 255),   # C - blue
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
                color=color.rgba32(255, 0, 0, 80),
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

        self.attacking_team = self.team_manager.red_team
        self.defending_team = self.team_manager.blue_team
        self.rounds_played = 0
        self.switch_message = None
        self.win_screen = None
        self.bomb_timer_ui = None
        self.on_round_start = None
        self.loadout_open = False
        self.bomb_plant_notif = None

        self.countdown_active = False
        self.countdown = 0
        self.countdown_text = None

        # Round-over banner state
        self.round_over_active = False
        self.round_over_timer = 0.0
        self.round_over_text = None
        self.pending_winner = None

        # Round timer
        self.round_time_left = ROUND_TIME

        # Timed action state
        self.action_type = None      # 'plant' or 'defuse'
        self.action_player = None
        self.action_timer = 0.0
        self._action_this_frame = False
        self._active_site_pos = None

        # Action progress HUD (only local player sees it — camera.ui)
        self.action_label = Text(
            text='',
            parent=camera.ui,
            position=(0, -0.40),
            origin=(0, 0),
            scale=2,
            color=color.white,
            enabled=False,
        )
        self.action_bar_bg = Entity(
            model='quad',
            parent=camera.ui,
            color=color.rgb32(40, 40, 40),
            scale=(0.35, 0.022),
            position=(0, -0.46),
            enabled=False,
        )
        self.action_bar_fill = Entity(
            model='quad',
            parent=camera.ui,
            color=color.yellow,
            scale=(0.001, 0.018),
            position=(-0.175, -0.46),
            origin=(-0.5, 0),
            enabled=False,
        )

        self.apply_team_colors()

    def start_round(self):
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
        self.round_time_left = ROUND_TIME

        self._reset_action()
        self.apply_team_colors()
        if self.on_round_start:
            self.on_round_start()
        self.start_countdown()

    def on_player_death(self, player):
        team = (
            self.team_manager.blue_team
            if player.team_color == self.team_manager.blue_team.color
            else self.team_manager.red_team
        )
        remaining = [p for p in team.players if not p.dead]
        if self.bomb_carrier == player and not self.bomb_planted:
            self.drop_bomb(player.position)
        if not remaining:
            # Bomb planted + all attackers dead → CTs must still defuse
            if self.bomb_planted and team is self.attacking_team:
                return
            winner = self.team_manager.get_opposing_team(player.team_color)
            self._award_round(winner)

    def _award_round(self, team):
        # Guard against double-award (e.g. bomb-explosion damage wiping CTs after the explicit award call)
        if self.round_over_active:
            return

        if team == self.team_manager.blue_team:
            self.blue_rounds += 1
        else:
            self.red_rounds += 1

        self.rounds_played += 1
        self.pending_winner = team

        # Show banner; transition logic runs after ROUND_OVER_DURATION
        self.round_over_active = True
        self.round_over_timer = ROUND_OVER_DURATION
        self._reset_action()

        team_name = 'BLUE' if team == self.team_manager.blue_team else 'RED'
        banner_color = color.azure if team == self.team_manager.blue_team else color.red
        if self.round_over_text:
            destroy(self.round_over_text)
        self.round_over_text = Text(
            text=f'{team_name} WINS THE ROUND',
            parent=camera.ui,
            origin=(0, 0),
            scale=3,
            background=True,
            color=banner_color,
            position=(0, 0.1),
        )

    def _advance_after_round_over(self):
        if self.round_over_text:
            destroy(self.round_over_text)
            self.round_over_text = None

        if self.rounds_played == self.round_limit - 1:
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
        if self.countdown_active:
            if not self.loadout_open:
                self.countdown -= time.dt
            remaining = math.ceil(self.countdown)
            if remaining > 0:
                self.countdown_text.text = str(remaining)
            if self.countdown <= 0:
                self.countdown_active = False
                destroy(self.countdown_text)
                self.countdown_text = None
            return

        # Round-over banner — freeze game logic, advance after duration
        if self.round_over_active:
            self.round_over_timer -= time.dt
            if self.round_over_timer <= 0:
                self.round_over_active = False
                self._advance_after_round_over()
            return

        # Round timer — only counts down before bomb is planted
        if not self.bomb_planted:
            self.round_time_left -= time.dt
            if self.round_time_left <= 0:
                self._award_round(self.defending_team)
                return

        # Bomb pickup
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

        # Bomb countdown after plant
        if self.bomb_planted:
            self.bomb_timer -= time.dt
            if self.bomb_timer_ui:
                remaining = max(0, math.ceil(self.bomb_timer))
                self.bomb_timer_ui.text = f'BOMB  {remaining}s'
                if self.bomb_timer > 10:
                    self.bomb_timer_ui.color = color.white
                    self.bomb_timer_ui.enabled = True
                elif self.bomb_timer > 5:
                    self.bomb_timer_ui.color = color.orange
                    self.bomb_timer_ui.enabled = True
                else:
                    self.bomb_timer_ui.color = color.red
                    self.bomb_timer_ui.enabled = int(self.bomb_timer * 4) % 2 == 0
            if self.bomb_timer <= 0:
                # Award first so round_over_active guards the on_player_death cascade
                self._award_round(self.planting_team)
                self._explode_bomb()
                return

        # Cancel action if handle_action wasn't called this frame
        if not self._action_this_frame:
            self._reset_action()
        self._action_this_frame = False

    def handle_action(self, player):
        if player.dead:
            return

        self._action_this_frame = True

        # Plant
        if (
            player == self.bomb_carrier
            and not self.bomb_planted
            and player.team_color == self.attacking_team.color
        ):
            for site in self.plant_sites:
                if distance(player.position, site.position) < BOMB_PLANT_RADIUS:
                    if self.action_type != 'plant' or self.action_player != player:
                        self.action_type = 'plant'
                        self.action_player = player
                        self.action_timer = 0.0
                        self._active_site_pos = site.position
                    self.action_timer += time.dt
                    self._update_action_hud('PLANTING...', self.action_timer / PLANT_TIME, color.orange)
                    if self.action_timer >= PLANT_TIME:
                        self.plant_bomb(player, self._active_site_pos)
                        self._reset_action()
                    return

        # Defuse
        if (
            self.bomb_planted
            and self.planted_bomb
            and distance(player.position, self.planted_bomb.position) < BOMB_DEFUSE_RADIUS
            and player.team_color != self.planting_team.color
        ):
            if self.action_type != 'defuse' or self.action_player != player:
                self.action_type = 'defuse'
                self.action_player = player
                self.action_timer = 0.0
            self.action_timer += time.dt
            self._update_action_hud('DEFUSING...', self.action_timer / DEFUSE_TIME, color.cyan)
            if self.action_timer >= DEFUSE_TIME:
                self.defuse_bomb(player)
                self._reset_action()
            return

        self._reset_action()

    def _update_action_hud(self, label, progress, bar_color=color.yellow):
        self.action_label.text = label
        self.action_label.enabled = True
        self.action_bar_bg.enabled = True
        self.action_bar_fill.enabled = True
        self.action_bar_fill.color = bar_color
        fill_w = max(0.001, min(0.35, 0.35 * progress))
        self.action_bar_fill.scale_x = fill_w

    def _reset_action(self):
        self.action_type = None
        self.action_player = None
        self.action_timer = 0.0
        self._active_site_pos = None
        self.action_label.enabled = False
        self.action_bar_bg.enabled = False
        self.action_bar_fill.enabled = False

    def plant_bomb(self, player, position):
        self.planted_bomb = Entity(
            model='cube', color=color.black, scale=0.5, position=position
        )
        self.bomb_planted = True
        self.planting_team = self.attacking_team
        self.bomb_timer = BOMB_TIMER
        self.bomb_carrier = None
        player.has_bomb = False

        if self.bomb_plant_notif:
            destroy(self.bomb_plant_notif)
        self.bomb_plant_notif = Text(
            text='BOMB PLANTED',
            parent=camera.ui,
            origin=(0, 0),
            scale=3,
            background=True,
            color=color.red,
        )
        destroy(self.bomb_plant_notif, delay=2)

        if self.bomb_timer_ui:
            destroy(self.bomb_timer_ui)
        self.bomb_timer_ui = Text(
            text=f'BOMB  {BOMB_TIMER}s',
            parent=camera.ui,
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
            parent=camera.ui,
            origin=(0, 0),
            scale=4,
            background=True,
            color=color.white,
        )

    def _explode_bomb(self):
        if not self.planted_bomb:
            return
        pos = Vec3(self.planted_bomb.position)

        # Damage everyone in blast radius — linear falloff
        for p in self.team_manager.all_players:
            if p.dead:
                continue
            d = distance(p.position, pos)
            if d < BOMB_BLAST_RADIUS:
                dmg = BOMB_BLAST_DAMAGE * (1.0 - d / BOMB_BLAST_RADIUS)
                p.take_damage(dmg, attacker=None)

        blast_colors = [color.orange, color.yellow, color.rgb32(255, 80, 0)]
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
            color=color.rgba32(255, 160, 50, 160),
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

        # Clean up any leftover round-over / action HUD before the win panel
        self._reset_action()
        if self.round_over_text:
            destroy(self.round_over_text)
            self.round_over_text = None
        if self.bomb_timer_ui:
            destroy(self.bomb_timer_ui)
            self.bomb_timer_ui = None

        self.win_screen = Entity(parent=camera.ui, ignore_paused=True)
        Panel(
            parent=self.win_screen,
            scale=(0.55, 0.4),
            color=color.rgba32(0, 0, 0, 200),
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
        self.round_over_active = False
        self.round_over_timer = 0.0
        self.pending_winner = None
        # Reset all players to AK47 at match start (AI re-randomises in respawn)
        for p in self.team_manager.all_players:
            p.selected_weapon = 'ak47'
        application.paused = False
        mouse.locked = True
        self.start_round()


# Global instance used throughout the game
sd_game = None
