from ursina import *
from gun import AK47, L96A1, M4A1, DSR1

ARMOUR_COST = 650


class BuyMenu(Entity):
    """Simple purchase menu for weapons and armour.

    The available weapons depend on the player's team colour.  The menu is
    toggled by pressing ``B`` and pauses the game while open.
    """

    def __init__(self, player):
        super().__init__(parent=camera.ui, enabled=False, ignore_paused=True)
        self.player = player
        Panel(parent=self, scale=(0.6, 0.5), color=color.rgba(0, 0, 0, 150))
        self.money_text = Text(parent=self, position=Vec2(-0.25, 0.2))
        self.buttons = []
        self._build_buttons()

    # ------------------------------------------------------------------
    def _build_buttons(self):
        weapons = []
        if self.player.team_color == color.red:
            weapons = [("AK-47", AK47), ("L96A1", L96A1)]
        else:
            weapons = [("M4A1", M4A1), ("DSR-1", DSR1)]

        y = 0.05
        for name, cls in weapons:
            btn = Button(
                text=f"{name} (${cls.cost})",
                parent=self,
                position=Vec2(0, y),
                on_click=lambda c=cls: self._buy_weapon(c),
            )
            self.buttons.append(btn)
            y -= 0.1

        armour_btn = Button(
            text=f"Armour (${ARMOUR_COST})",
            parent=self,
            position=Vec2(0, y),
            on_click=self._buy_armour,
        )
        self.buttons.append(armour_btn)

    # ------------------------------------------------------------------
    def toggle(self):
        if self.enabled:
            self.close()
        else:
            self.open()

    def open(self):
        for b in self.buttons:
            destroy(b)
        self.buttons.clear()
        self._build_buttons()
        self.enabled = True
        mouse.locked = False
        self.update_money()

    def close(self):
        self.enabled = False
        mouse.locked = True

    def update_money(self):
        self.money_text.text = f"Money: ${int(self.player.money)}"

    # ------------------------------------------------------------------
    def _buy_weapon(self, weapon_cls):
        cost = weapon_cls.cost
        if self.player.money >= cost:
            self.player.money -= cost
            self.player.equip_gun(weapon_cls)
            self.update_money()

    def _buy_armour(self):
        if self.player.money >= ARMOUR_COST:
            self.player.money -= ARMOUR_COST
            self.player.buy_armour()
            self.update_money()
