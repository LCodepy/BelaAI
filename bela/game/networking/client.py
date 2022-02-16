import time
from enum import Enum
from typing import Any

import pygame

from bela.game.ui.button import Button
from bela.game.utils.assets import Assets
from ..ui.label import Label
from ..utils import config
from ..events.events import EventHandler
from ..networking.network import Network
from ..utils.colors import Color

pygame.init()
pygame.font.init()
pygame.mixer.init()


class Client:

    def __init__(self):

        self.network = Network(buffer=4096)
        self.network.connect()

        self.network.update_connection()

        self.__player = int(self.network.player_id)
        self.__game_id = int(self.network.game_id)
        self.__nickname = "TEMP"  # TODO: replace

        self.network.send_only(self.__nickname)

        self.win = pygame.display.set_mode(config.WINDOW_SIZE, pygame.SRCALPHA)
        pygame.display.set_caption(f"Bela - Client {self.__player} | Game {self.__game_id}")

        self.canvas = pygame.Surface(config.WINDOW_SIZE, pygame.SRCALPHA)

        # Event Handler

        self.event_handler = EventHandler()

        # Assets

        self.assets = Assets()

        # GUI Elements

        self.title = Label(
            self.display,
            (520, 180),
            (300, 200),
            pygame.font.SysFont("comicsans", 210),
            text="BELA",
            font_color=Color.white,
            bold=True
        )

        self.play_btn = Button(
            self.display,
            (0, 530),
            (720, 95),
            self.assets.font32,
            center_x=False,
            text="PLAY",
            font_color=Color.white,
            img=self.assets.default_btn_shadow,
            bold=True,
            text_orientation="left",
            padding=40
        )

        self.options_btn = Button(
            self.display,
            (-100, 450),
            (720, 95),
            self.assets.font32,
            center_x=False,
            text="OPTIONS",
            font_color=Color.white,
            img=self.assets.default_btn_shadow,
            bold=True,
            text_orientation="left",
            padding=140
        )

        # Variables

        self.clock = pygame.time.Clock()
        self.__fps = 60

        self.pressed_point = None
        self.winner = None
        self.data: dict[str, Any] = {"game": None}

        """-----------------------------------MAIN LOOP---------------------------------"""
        while True:

            self.update()
            self.render()

            if not self.event_handler.loop():
                break

        pygame.quit()

    def on_turn(self):
        return self.__player == self.game.player_turn

    def update(self):
        self.data = self.network.send("get")

        # Buttons

    def render(self):
        self.win.fill(Color.white)
        self.canvas.fill((0, 0, 20))

        # Draw here

        if self.game.is_ready():
            self.render_game()
        else:
            self.render_menu()

        self.win.blit(self.canvas, (0, 0))

        pygame.display.update()
        self.clock.tick(self.__fps)

    def render_game(self) -> None:
        pass

    def render_menu(self) -> None:
        self.title.render()
        self.play_btn.render()
        self.options_btn.render()

    def get_assets(self) -> Assets:
        return self.assets

    @property
    def game(self) -> Any:
        return self.data["game"]

    @property
    def display(self) -> pygame.Surface:
        return self.canvas


if __name__ == "__main__":
    client = Client()
