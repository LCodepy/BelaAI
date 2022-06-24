import time
from enum import Enum
from typing import Any

import pygame

from bela.game.networking.commands import Commands
from bela.game.ui.button import Button
from bela.game.utils.assets import Assets
from bela.game.utils.timer import TimerHandler
from ..ui.label import Label
from ..utils import config
from ..events.events import EventHandler
from ..networking.network import Network
from ..utils.colors import *

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

        # Variables

        self.clock = pygame.time.Clock()
        self.__fps = 60

        self.pressed_point = None
        self.winner = None
        self.data: dict[str, Any] = {"game": None}

        self.label_dots = 0

        # Event functions

        def on_play_btn_click(cls, x, y):
            cls.data = cls.network.send(Commands.READY_UP)
            cls.timer_handler.add_timer("dots1", 0.8, update_label_text1, cls)

        def on_options_btn_click(cls, x, y):
            pass

        def update_label_text1(cls):
            cls.label_dots += 1
            if cls.label_dots > 3:
                cls.label_dots = 1
            cls.waiting_lobby_label.set_text("Pričekajte" + "." * cls.label_dots)
            cls.timer_handler.add_timer_during_exec("dots2", 0.8, update_label_text1, cls)

        # Timers

        self.timer_handler = TimerHandler()

        # GUI Elements

        self.title = Label(
            self.display,
            (520, 180),
            (300, 200),
            pygame.font.SysFont("comicsans", 210),
            text="BELA",
            font_color=Colors.white,
            bold=True
        )

        self.play_btn = Button(
            self.display,
            (0, 530),
            (650, 70),
            self.assets.font32,
            center_x=False,
            text="IGRAJ",
            color=Colors.black,
            font_color=Colors.white,
            bold=True,
            text_orientation="left",
            padding=40
        ).set_on_click_listener(on_play_btn_click, self)

        self.options_btn = Button(
            self.display,
            (-100, 450),
            (650, 70),
            self.assets.font32,
            center_x=False,
            text="OPCIJE",
            color=Colors.black,
            font_color=Colors.white,
            bold=True,
            text_orientation="left",
            padding=140
        ).set_on_click_listener(on_options_btn_click, self)

        self.waiting_lobby_label = Label(
            self.display,
            (self.display.get_width() // 2, self.display.get_height() // 2),
            (400, 200),
            pygame.font.SysFont("comicsans", 100),
            text="Pričekajte",
            font_color=Colors.white,
            bold=True,
        )

        self.player_count_label = Label(
            self.display,
            (self.display.get_width() // 2, self.display.get_height() // 2 + 80),
            (700, 200),
            self.assets.font48,
            text="Spremni igrači: 0/4",
            font_color=Colors.light_grey,
            bold=True,
        )

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
        self.data = self.network.send(Commands.GET)

        self.timer_handler.update()

        if self.game.is_ready():
            self.update_game()
        elif self.game.is_player_ready(self.__player):
            self.update_lobby()
        else:
            self.update_menu()

    def update_game(self) -> None:
        pass

    def update_menu(self) -> None:
        self.play_btn.update(self.event_handler)
        self.options_btn.update(self.event_handler)

    def update_lobby(self) -> None:
        self.player_count_label.set_text("Spremni igrači: " + str(self.game.get_ready_player_count()) + "/4")

    def render(self):
        self.win.fill(Colors.white.c)
        self.canvas.fill((0, 0, 20))

        # Draw here

        if self.game.is_ready():
            self.render_game()
        elif self.game.is_player_ready(self.__player):
            self.render_lobby()
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

    def render_lobby(self) -> None:
        self.canvas.fill(Color(9, 21, 49).c)

        self.waiting_lobby_label.render()
        self.player_count_label.render()

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
