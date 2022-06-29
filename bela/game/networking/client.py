import math
import random
import time
from enum import Enum
from typing import Any

import pygame

from bela.game.main.bela import GameState, Hand, Card
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
        self.__nickname = f"PLAYER {self.__player}"

        self.network.send_only(self.__nickname)

        self.win = pygame.display.set_mode(config.WINDOW_SIZE, pygame.SRCALPHA)
        pygame.display.set_caption(f"Bela - Client {self.__player} | Game {self.__game_id}")

        self.canvas = pygame.Surface(config.CANVAS_SIZE, pygame.SRCALPHA)
        self.info_canvas = pygame.Surface(config.INFO_CANVAS_SIZE, pygame.SRCALPHA)

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

        self.player_positions = [(280, 500), (530, 500), (530, 100), (280, 100)]
        self.card_positions = [(280, 500), (530, 500)]
        self.talon_card_positions = [(280, 330), (530, 330)]
        self.inventory = []
        self.inventory_calculated = False
        self.moving_card = None
        self.card_area = pygame.Rect(350, 240, 100, 80)

        # Event functions

        def on_play_btn_click(cls, x, y):
            cls.data = cls.network.send(Commands.READY_UP)
            cls.timer_handler.add_timer("dots1", 0.8, update_label_text1, cls)

        def on_options_btn_click(cls, x, y):
            pass

        def on_sort_cards_btn_click(cls, x, y):
            cls.data = cls.network.send(Commands.SORT_CARDS)
            if cls.game.get_current_game_state() == GameState.ZVANJE_ADUTA and not cls.game.dalje[cls.__player]:
                cls.calculate_card_positions(cls.game.get_netalon(cls.get_player()))
            else:
                cls.calculate_card_positions(cls.get_cards().sve)

        def update_label_text1(cls):
            cls.label_dots += 1
            if cls.label_dots > 3:
                cls.label_dots = 1
            cls.waiting_lobby_label.set_text("Pričekajte" + "." * cls.label_dots)
            cls.timer_handler.add_timer_during_exec("dots2", 0.8, update_label_text1, cls)

        def on_adut_btn_click(cls, x, y, btn):
            if cls.game.get_current_game_state() == GameState.ZVANJE_ADUTA:
                cls.data = cls.network.send(Commands.new(Commands.CALL_ADUT, btn.text))
                cls.calculate_card_positions(cls.get_cards().sve)

        def on_dalje_btn_click(cls, x, y):
            if cls.game.get_current_game_state() == GameState.ZVANJE_ADUTA:
                cls.data = cls.network.send(Commands.DALJE)
                cls.calculate_card_positions(cls.get_cards().sve)

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

        self.sort_cards_button = Button(
            self.display,
            (120, 550),
            (160, 30),
            self.assets.font18,
            text="SORTIRAJ KARTE",
            font_color=Colors.white
        ).set_on_click_listener(on_sort_cards_btn_click, self)

        types = ["karo", "pik", "herc", "tref"]
        self.call_adut_buttons = [
            Button(
                self.display,
                (self.display.get_width() // 2 + 100 * (0.5 - i), self.display.get_height() // 2),
                (50, 50),
                self.assets.font18,
                text=types[i+1],
                font_color=Colors.white
            ).set_on_click_listener(on_adut_btn_click, self, pass_self=True) for i in range(-1, 3)
        ]

        self.dalje_button = Button(
            self.display,
            (self.display.get_width() // 2, self.display.get_height() // 2 + 70),
            (70, 36),
            self.assets.font18,
            text="DALJE",
            font_color=Colors.white
        ).set_on_click_listener(on_dalje_btn_click, self)

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

        if not self.game.is_player_ready(self.__player):
            self.update_menu()

        if self.game.is_ready():
            self.update_game()
        elif self.game.is_player_ready(self.__player):
            self.update_lobby()

    def update_game(self) -> None:
        self.update_cards()

        self.sort_cards_button.update(self.event_handler)

        if self.game.get_current_game_state() is GameState.ZVANJE_ADUTA:
            if not self.inventory_calculated:
                self.calculate_card_positions(self.game.get_netalon(self.__player), 100)
            if (
                    self.game.get_adut() is None and
                    self.game.player_turn == self.__player and
                    not self.game.dalje[self.__player]
            ):
                self.update_calling_adut()

        if self.game.get_current_game_state() is GameState.ZVANJA:
            if len(self.inventory) == 6 or not self.inventory:
                self.calculate_card_positions(self.get_cards().sve, 100)

    def update_calling_adut(self) -> None:
        for button in self.call_adut_buttons:
            button.update(self.event_handler)
        if self.game.count_dalje < 3:
            self.dalje_button.update(self.event_handler)

    def update_menu(self) -> None:
        self.play_btn.update(self.event_handler)
        self.options_btn.update(self.event_handler)

    def update_lobby(self) -> None:
        self.player_count_label.set_text("Spremni igrači: " + str(self.game.get_ready_player_count()) + "/4")

    def update_cards(self) -> None:
        for i, card in enumerate(self.inventory):
            if (
                    self.event_handler.held["left"] and
                    card.rect.collidepoint(self.event_handler.get_pos()) and
                    self.moving_card is None
            ):
                self.moving_card = i

            if self.moving_card == i:
                self.inventory[i].set_pos(self.event_handler.get_pos())

        if (
                self.event_handler.releases["left"] and
                self.moving_card is not None
        ):
            if self.card_area.collidepoint(self.inventory[self.moving_card].get_pos()):
                card_passed = self.network.send(Commands.new(Commands.PLAY_CARD, self.inventory[self.moving_card]))
                self.data = self.network.recv_only()
                if card_passed:
                    self.inventory.pop(self.moving_card)
                else:
                    self.inventory[self.moving_card].move_back()
            else:
                for i, card in enumerate(self.inventory):
                    if card.collision_rect().collidepoint(self.inventory[self.moving_card].get_pos()) and i != self.moving_card:
                        self.inventory[self.moving_card].move_back()
                        c1 = self.game.get_card_index(self.__player, self.inventory[self.moving_card].card)
                        c2 = self.game.get_card_index(self.__player, self.inventory[i].card)
                        self.data = self.network.send(Commands.new(Commands.SWAP_CARDS, (c1, c2)))
                        self.inventory[self.moving_card].card, self.inventory[i].card = self.inventory[i].card, self.inventory[self.moving_card].card
                        break
                else:
                    self.inventory[self.moving_card].move_back()
            self.moving_card = None

    def render(self):
        self.win.fill(Colors.white.c)
        self.canvas.fill((0, 0, 20))
        self.info_canvas.fill((0, 0, 20))

        # Draw here

        if self.game.is_ready():
            self.render_game()
        elif self.game.is_player_ready(self.__player):
            self.render_lobby()
        else:
            self.render_menu()

        self.render_info()

        self.win.blit(self.canvas, (0, 0))
        self.win.blit(self.info_canvas, (self.canvas.get_width(), 0))

        pygame.display.update()
        self.clock.tick(self.__fps)

    def render_info(self) -> None:
        pygame.draw.line(self.info_canvas, (70, 110, 150), (0, 8), (0, self.info_canvas.get_height() - 8))

        if not self.game.is_ready():
            return
        Label.render_text(self.info_canvas, "INFO PANEL", (10, 10), self.assets.font24, (255, 255, 255), centered=False)
        pygame.draw.line(self.info_canvas, (70, 110, 150), (8, 30), (self.info_canvas.get_width() - 8, 30))
        Label.render_text(
            self.info_canvas,
            "NA POTEZU: " + str(self.game.player_data[self.game.player_turn]["nickname"]),
            (10, 40), self.assets.font18, (200, 200, 200), centered=False
        )
        Label.render_text(
            self.info_canvas, "ADUT: " + str(self.game.adut), (10, 60), self.assets.font18, (200, 200, 200), centered=False
        )

    def render_game(self) -> None:
        self.canvas.blit(self.assets.table, (self.canvas.get_width() // 2 - self.assets.table.get_width() // 2,
                                             self.canvas.get_height() // 2 - self.assets.table.get_height() // 2))

        self.render_players()
        self.render_hand()

        self.sort_cards_button.render()

        if (
                self.game.get_current_game_state() is GameState.ZVANJE_ADUTA and
                self.game.get_adut() is None and
                self.game.player_turn == self.__player and
                not self.game.dalje[self.__player]
        ):
            self.render_calling_adut()

    def render_calling_adut(self) -> None:
        surf = pygame.Surface(self.display.get_size(), pygame.SRCALPHA)
        surf.fill((0, 0, 0))
        surf.set_alpha(100)
        self.display.blit(surf, (0, 0))

        for button in self.call_adut_buttons:
            button.render()

        if self.game.count_dalje < 3:
            self.dalje_button.render()

    def render_menu(self) -> None:
        self.title.render()
        self.play_btn.render()
        self.options_btn.render()

    def render_lobby(self) -> None:
        self.canvas.fill(Color(9, 21, 49).c)

        self.waiting_lobby_label.render()
        self.player_count_label.render()

    def render_players(self) -> None:
        for i in range(4):
            x, y = self.player_positions[i]
            if self.__player % 2:
                x, y = self.player_positions[i+1 if i < 3 else 0]
            idx = self.__player + i
            if idx >= 4:
                idx = self.__player + i - 4
            pygame.draw.circle(self.canvas, (0, 0, 0), (x, y), 30)
            if self.__player == idx:
                pygame.draw.circle(self.canvas, (200, 200, 0), (x, y), 30)
            pygame.draw.circle(self.canvas, (100, 100, 100), (x, y), 30, 4)
            Label.render_text(self.canvas, "Ti" if idx == self.__player else self.game.get_nickname(idx),
                              (x, y + 70 * (not int(idx < 2) if self.__player > 1 else int(idx < 2)) - 35),
                              self.assets.font24, (255, 255, 255), bold=True)

    def render_hand(self) -> None:
        if self.game.get_current_game_state() is GameState.ZVANJE_ADUTA and not self.game.dalje[self.__player]:
            self.render_cards(self.game.get_netalon(self.__player))
        elif self.game.get_current_game_state() is GameState.ZVANJA or self.game.dalje[self.__player]:
            self.render_cards(self.get_cards().sve)

    def render_cards(self, cards: list) -> None:
        for card in self.game.cards_on_table:
            if card is not None:
                self.canvas.blit(pygame.transform.rotate(self.assets.card_images[card.card], -82-card.angle),
                                 (card.x - card.rect.w // 2, card.y - card.rect.h // 2))

        self.render_player_cards()

        for i, card in enumerate(cards):
            if i == self.moving_card:
                continue
            x = self.inventory[i].x
            y = self.inventory[i].y
            alfa = self.inventory[i].angle
            card = pygame.transform.rotate(self.assets.card_images[card], -82 - alfa)
            self.canvas.blit(card, (x - card.get_width() // 2, y - card.get_height() // 2))

        if self.moving_card is not None:
            card = self.inventory[self.moving_card]
            self.canvas.blit(
                img := pygame.transform.rotate(self.assets.card_images[card.card], -82 - card.angle),
                (card.x - img.get_width() // 2, card.y - img.get_height() // 2)
            )

    def render_player_cards(self) -> None:
        k = 15
        r = 100

        # Cards in talon
        for p in range(4):
            if self.game.dalje[p] or self.game.get_current_game_state() is not GameState.ZVANJE_ADUTA:
                continue
            card = pygame.transform.rotate(self.assets.card_back, 90)
            x, y = self.talon_card_positions[p in (0, 3)]
            rot = p < 2
            if self.__player < 2:
                x, y = self.talon_card_positions[p not in (0, 3)]
                rot = p >= 2
            if rot:
                y -= 60

            self.canvas.blit(card, (x - card.get_width() // 2, y - card.get_height() // 2 - 3))
            self.canvas.blit(card, (x - card.get_width() // 2, y - card.get_height() // 2 + 3))

        # Cards in hand
        for p in range(4):
            if p == self.__player:
                continue
            x0, y0 = self.card_positions[p in (0, 3)]
            rot = p < 2
            if self.__player < 2:
                x0, y0 = self.card_positions[p not in (0, 3)]
                rot = p >= 2
            if rot:
                y0 -= 400

            cards = self.game.get_netalon(p) if self.game.get_current_game_state() is GameState.ZVANJE_ADUTA else self.game.cards[p].sve
            alfa = (98 if rot else -82) - len(cards) * k // 2
            for _ in cards:
                x = int(math.cos(math.radians(alfa)) * r)
                y = int(math.sin(math.radians(alfa)) * r)
                alfa += k
                card = pygame.transform.rotate(self.assets.card_back, (98 if rot else -82) - alfa)
                self.canvas.blit(card, (x0 + x - card.get_width()//2, y0 + y - card.get_height()//2))

    def calculate_card_positions(self, cards: list, r: int = 100, k: int = 15) -> None:
        self.inventory = []
        x0, y0 = self.card_positions[self.__player % 2]
        alfa = -82 - len(cards) * k // 2
        for card in cards:
            x = math.cos(math.radians(alfa)) * r
            y = math.sin(math.radians(alfa)) * r
            alfa += k
            self.inventory.append(
                Card(card, int(x0 + x), int(y0 + y), alfa, pygame.Rect(
                    int(x0 + x) - self.assets.card_width // 2, int(y0 + y) - self.assets.card_height // 2,
                    self.assets.card_width, self.assets.card_height
                ))
            )
        self.inventory_calculated = True

    def get_cards(self) -> Hand:
        return self.game.cards[self.__player]

    def get_player(self) -> int:
        return self.__player

    @property
    def game(self) -> Any:
        return self.data["game"]

    @property
    def display(self) -> pygame.Surface:
        return self.canvas


if __name__ == "__main__":
    client = Client()
