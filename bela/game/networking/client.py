import copy
import math
import random
import time
from itertools import chain
from typing import Any

import pygame

from bela.game.main.bela import GameState, Hand, Card
from bela.game.networking.commands import Commands
from bela.game.ui.button import Button
from bela.game.utils.assets import Assets
from bela.game.utils.shapes import RotatingRect
from bela.game.utils.timer import TimerHandler
from ..ui.label import Label
from ..utils import config, rendering
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

        self.timed_actions_before_canvas = pygame.Surface(self.canvas.get_size(), pygame.SRCALPHA)
        self.timed_actions_after_canvas = pygame.Surface(self.canvas.get_size(), pygame.SRCALPHA)

        # Event Handler

        self.event_handler = EventHandler()

        # Assets

        self.assets = Assets()

        # Variables

        self.clock = pygame.time.Clock()
        self.__fps = 60

        self.data: dict[str, Any] = {"game": None}

        self.label_dots = 0

        self.player_positions = [(270, 500), (530, 500), (530, 100), (270, 100)]
        self.card_positions = [(270, 500), (530, 500)]
        self.talon_card_positions = [(280, 330), (530, 330)]
        self.gained_stihovi_positions = [(200, 350), (600, 350), (600, 250), (200, 250)]
        self.gained_stihovi_angles = [-45, 45, -45, 45]
        self.cards_on_table_positions_p1 = []
        self.cards_on_table_positions_p2 = []
        self.zvanja_card_positions = [(280, 330), (530, 330), (530, 270), (280, 270)]
        self.zvanja_card_offsets = {}
        self.card_area = pygame.Rect(350, 240, 100, 80)

        self.inventory = []
        self.inventory_calculated = False

        self.cards_on_table = []
        self.moving_card = None
        self.selected_cards = [False for _ in range(8)]
        self.selected_cards_for_bela = [None, None]

        self.adut_dalje = False
        self.zvanja_dalje = False
        self.called_zvanje = False
        self.zvanja_timer_created = False
        self.calling_bela = False

        self.switched_cards = []
        self.switched_cards_marker_color = (0, 255, 0, 0)
        self.placed_card_marker_color = (0, 0, 255, 0)
        self.called_bela_marker_color = (255, 0, 0, 0)

        self.activated_turn_end = False
        self.activated_game_over = False
        self.end_game = False

        self.score_y_offset = 15

        self.last_frame_cards_on_table = []

        self.timed_actions = [{}, {}]

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
                cls.adut_dalje = True

        def on_nema_zvanja_btn_click(cls, x, y):
            cls.zvanja_dalje = True
            cls.data = cls.network.send(Commands.new(Commands.ZVANJE, []))
            cls.recheck_zvanja()

        def on_ima_zvanja_btn_click(cls, x, y):
            cards = []
            for i, v in enumerate(cls.selected_cards):
                if v:
                    cards.append(cls.inventory[i].card)
            cls.data = cls.network.send(Commands.new(Commands.ZVANJE, cards))
            if cls.game.zvanja[cls.__player]:
                cls.called_zvanje = True
            else:
                cls.zvanja_dalje = True
            cls.recheck_zvanja()

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
                text=types[i + 1],
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

        self.nema_zvanja_button = Button(
            self.display,
            (self.display.get_width() // 2 - 100, self.display.get_height() // 2),
            (140, 30),
            self.assets.font18,
            text="NEMAM ZVANJA",
            font_color=Colors.white
        ).set_on_click_listener(on_nema_zvanja_btn_click, self)

        self.ima_zvanja_button = Button(
            self.display,
            (self.display.get_width() // 2 + 100, self.display.get_height() // 2),
            (140, 30),
            self.assets.font18,
            text="ZOVEM",
            font_color=Colors.white
        ).set_on_click_listener(on_ima_zvanja_btn_click, self)

        self.zvanja_label = Label(
            self.display,
            (self.display.get_width() // 2, self.display.get_height() // 2 - 60),
            (400, 100),
            self.assets.font32,
            text="OZNAČITE ZVANJA",
            font_color=Colors.white
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

        self.update_timed_actions()

        if not self.game.is_player_ready(self.__player):
            self.update_menu()

        if self.game.is_ready():
            self.update_game()
        elif self.game.is_player_ready(self.__player):
            self.update_lobby()

    def update_game(self) -> None:
        if self.game.current_game_over and not self.activated_game_over:
            self.timed_actions[1]["GAME_OVER"] = [True, time.time()]
            self.activated_game_over = True

        if not self.game.current_game_over:
            self.activated_game_over = False

        self.sync_inventory()

        self.update_score()

        self.update_cards()

        self.sort_cards_button.update(self.event_handler)

        if self.end_game:
            self.end_current_game()
            self.end_game = False

        if self.game.get_current_game_state() is GameState.ZVANJE_ADUTA:
            if not self.inventory_calculated:
                self.calculate_card_positions(self.game.get_netalon(self.__player))
            if (
                    self.game.get_adut() is None and
                    self.game.player_turn == self.__player and
                    not self.game.dalje[self.__player]
            ):
                self.update_calling_adut()

        if self.game.get_current_game_state() is GameState.ZVANJA and len(self.inventory) in (0, 6):
            self.calculate_card_positions(self.get_cards().sve)

        if self.game.get_current_game_state() is GameState.ZVANJA:
            if not self.zvanja_dalje and not self.called_zvanje:
                self.update_zvanja()
            elif self.game.get_zvanje_state() == 1:
                if not self.zvanja_timer_created:
                    countdown = 4
                    if not any(self.game.zvanja):
                        countdown = 0
                    self.timer_handler.add_timer_during_exec("SHOW_ZVANJA", countdown, self.finish_zvanja, self)
                    self.zvanja_timer_created = True
                self.update_game_zvanje()

    def update_score(self) -> None:
        if not pygame.Rect(35, 210, self.info_canvas.get_width() - 70, 240).collidepoint(self.event_handler.get_pos()):
            return

        if self.event_handler.scrolls["up"]:
            self.score_y_offset = min(self.score_y_offset + 10, 15)
        elif self.event_handler.scrolls["down"]:
            self.score_y_offset = max(self.score_y_offset - 10, 15 - (max(len(self.game.games), 5) - 5) * 25)

    def update_calling_adut(self) -> None:
        for button in self.call_adut_buttons:
            button.update(self.event_handler)

        if self.game.count_dalje < 3:
            self.dalje_button.update(self.event_handler)

    def update_zvanja(self) -> None:
        self.ima_zvanja_button.update(self.event_handler)
        self.nema_zvanja_button.update(self.event_handler)

        for i, card in enumerate(reversed(self.inventory)):
            if self.event_handler.presses["right"] and card.rect.collidepoint(self.event_handler.get_pos()):
                self.selected_cards[len(self.inventory) - i - 1] = not self.selected_cards[len(self.inventory) - i - 1]
                break

    def update_game_zvanje(self) -> None:
        pass

    def update_menu(self) -> None:
        self.play_btn.update(self.event_handler)
        self.options_btn.update(self.event_handler)

    def update_lobby(self) -> None:
        self.player_count_label.set_text("Spremni igrači: " + str(self.game.get_ready_player_count()) + "/4")

    def update_cards(self) -> None:
        self.update_cards_in_inventory()

        if self.game.turn_just_ended and not self.activated_turn_end:
            self.timed_actions[0]["TURN_ENDED"] = [True, time.time()]
            self.cards_on_table = copy.deepcopy(self.game.cards_on_table)
            self.activated_turn_end = True

        if (
                len(self.game.cards_on_table) != len(self.last_frame_cards_on_table)
                and self.game.cards_on_table
        ):
            self.timed_actions[0]["DISPLAY_CARD_PLAYED"] = [True, time.time(), self.game.cards_on_table[-1]]

        if self.event_handler.releases["left"] and self.moving_card is not None:
            if self.card_area.collidepoint(self.inventory[self.moving_card].get_pos()):
                self.handle_card_playing()
            else:
                self.handle_card_swapping()
            self.moving_card = None

        self.last_frame_cards_on_table = self.game.cards_on_table

    def update_cards_in_inventory(self) -> None:
        for i, card in enumerate(reversed(self.inventory)):
            if (
                    self.game.get_current_game_state() is GameState.ZVANJA and
                    self.game.get_zvanje_state() == 1 and
                    card.card in list(chain(*self.game.get_player_zvanja(self.__player)))
            ):
                continue

            i = len(self.inventory) - i - 1

            if (
                    self.event_handler.presses["right"] and
                    card.rect.collidepoint(self.event_handler.get_pos()) and
                    self.game.get_current_game_state() is GameState.IGRA and
                    self.on_turn() and self.moving_card is None and
                    card.card in [("baba", self.game.get_adut()), ("kralj", self.game.get_adut())] and
                    self.game.player_has_bela(self.__player)
            ):
                idx = 0
                for x, c in enumerate(self.inventory):
                    if c.card in (("kralj", self.game.get_adut()), ("baba", self.game.get_adut())):
                        self.selected_cards_for_bela[idx] = x
                        idx = 1
                if None in self.selected_cards_for_bela:
                    self.selected_cards_for_bela = [None, None]
                else:
                    self.timed_actions[0]["CALL_BELA"] = [True, time.time()]
                    self.calling_bela = True
                break

            if (
                    self.event_handler.held["left"] and
                    card.rect.collidepoint(self.event_handler.get_pos()) and
                    self.moving_card is None and
                    ("MOVE_BACK_CARD" not in self.timed_actions[0] or
                     not self.timed_actions[0]["MOVE_BACK_CARD"][0]) and
                    ("CALL_BELA" not in self.timed_actions[0] or
                     not self.timed_actions[0]["CALL_BELA"][0])
            ):
                self.moving_card = i

            if self.moving_card == i:
                self.inventory[i].set_pos(self.event_handler.get_pos())

    def handle_card_playing(self) -> None:
        card_passed = self.network.send(Commands.new(Commands.PLAY_CARD, self.inventory[self.moving_card]))
        self.data = self.network.recv_only()
        if card_passed:
            self.inventory.pop(self.moving_card)
            if self.calling_bela and None not in self.selected_cards_for_bela:
                self.data = self.network.send(Commands.CALLED_BELA)
                self.calling_bela = False
            self.selected_cards_for_bela = [None, None]
            if self.game.cards_on_table:
                self.timed_actions[0]["DISPLAY_CARD_PLAYED"] = [True, time.time(), self.game.cards_on_table[-1]]
        else:
            self.timed_actions[0]["MOVE_BACK_CARD"] = [True, time.time(), self.moving_card,
                                                       copy.deepcopy(self.inventory[self.moving_card])]
            self.timed_actions[1]["DISPLAY_CARD_ERROR"] = [True, time.time()]

    def handle_card_swapping(self) -> None:
        for i, card in enumerate(self.inventory):
            if (
                    self.game.get_current_game_state() is GameState.ZVANJA and
                    self.game.get_zvanje_state() == 1 and
                    card.card in list(chain(*self.game.get_player_zvanja(self.__player)))
            ):
                continue
            if (
                    card.collision_rect().collidepoint(self.inventory[self.moving_card].get_pos()) and
                    i != self.moving_card
            ):
                self.inventory[self.moving_card].move_back()
                c1 = self.game.get_card_index(self.__player, self.inventory[self.moving_card].card)
                c2 = self.game.get_card_index(self.__player, self.inventory[i].card)

                self.data = self.network.send(Commands.new(Commands.SWAP_CARDS, (c1, c2)))

                self.inventory[self.moving_card].card, self.inventory[i].card = \
                    self.inventory[i].card, self.inventory[self.moving_card].card
                self.selected_cards[self.moving_card], self.selected_cards[i] = \
                    self.selected_cards[i], self.selected_cards[self.moving_card]

                self.switched_cards = [self.moving_card, i]
                self.timed_actions[0]["SWITCH_CARDS"] = [True, time.time()]
                break
        else:
            self.timed_actions[0]["MOVE_BACK_CARD"] = [True, time.time(), self.moving_card,
                                                       copy.deepcopy(self.inventory[self.moving_card])]

    def update_timed_actions(self) -> None:
        to_remove = []
        to_add = []
        for action, args in self.timed_actions[0].items():
            t = time.time()

            if action == "MOVE_BACK_CARD" and args[0] and t - args[1] < 1:
                self.move_back_card(t - args[1], args[2], args[3])

            if action == "SWITCH_CARDS" and args[0]:
                if t - args[1] < 1:
                    self.switch_card_unmark(t - args[1])
                elif t - args[1] > 1:
                    self.switched_cards = []
                    to_remove.append("SWITCH_CARDS")

            if action == "DISPLAY_CARD_PLAYED" and args[0]:
                if t - args[1] < 0.8:
                    self.placed_card_unmark(t - args[1])
                elif t - args[1] > 0.8:
                    to_remove.append("DISPLAY_CARD_PLAYED")

            if action == "CALL_BELA" and args[0]:
                if t - args[1] < 1:
                    self.called_bela_unmark(t - args[1])
                elif t - args[1] > 1:
                    to_remove.append("CALL_BELA")

            if action == "TURN_ENDED" and args[0]:
                if t - args[1] < 2:
                    self.move_removed_cards(t - args[1])
                elif t - args[1] > 2:
                    self.cards_on_table_positions_p1 = []
                    self.cards_on_table_positions_p2 = []
                    self.cards_on_table = []
                    self.activated_turn_end = False
                    to_remove.append("TURN_ENDED")
                    self.data = self.network.send(Commands.END_TURN)

        for rem in to_remove:
            self.timed_actions[0].pop(rem)

        for add in to_add:
            self.timed_actions[0][add[0]] = add[1]

    def render(self) -> None:
        self.win.fill(Colors.white.c)
        self.canvas.fill((0, 0, 20))
        self.info_canvas.fill((0, 0, 20))

        # Draw here

        self.render_timed_actions()

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
        Label.render_text(self.info_canvas, "INFO", (10, 10), self.assets.font24, (255, 255, 255), centered=False)
        pygame.draw.line(self.info_canvas, (70, 110, 150), (8, 30), (self.info_canvas.get_width() - 8, 30))
        Label.render_text(
            self.info_canvas,
            "NA POTEZU: " + str(self.game.player_data[self.game.player_turn]["nickname"]
                                if self.game.player_turn != -1 else ""),
            (10, 40), self.assets.font18, (200, 200, 200), centered=False
        )
        Label.render_text(
            self.info_canvas, "ADUT: " + str(self.game.adut), (10, 60), self.assets.font18, (200, 200, 200),
            centered=False
        )
        Label.render_text(
            self.info_canvas, "GAMESTATE: " + str(self.game.get_current_game_state()).split(".")[1], (10, 80),
            self.assets.font18, (200, 200, 200), centered=False
        )

        Label.render_text(self.info_canvas, "BODOVI", (10, 140), self.assets.font24, (255, 255, 255), centered=False)
        pygame.draw.line(self.info_canvas, (70, 110, 150), (8, 160), (self.info_canvas.get_width() - 8, 160))

        self.render_score()

    def render_score(self) -> None:
        y = 200
        pygame.draw.rect(self.info_canvas, (10, 30, 50), [35, y - 20, self.info_canvas.get_width() - 70, 30])

        Label.render_text(self.info_canvas, "MI", ((self.info_canvas.get_width() + 70) // 4, y),
                          self.assets.font24, (255, 255, 255))
        Label.render_text(self.info_canvas, "VI", ((3 * self.info_canvas.get_width() - 70) // 4, y),
                          self.assets.font24, (255, 255, 255))

        pygame.draw.line(self.info_canvas, (70, 110, 150), (35, y + 10), (self.info_canvas.get_width() - 35, y + 10))
        pygame.draw.line(self.info_canvas, (70, 110, 150), (self.info_canvas.get_width() // 2, y - 20),
                         (self.info_canvas.get_width() // 2, y + 240))

        surf = pygame.Surface((self.info_canvas.get_width() - 60, 300), pygame.SRCALPHA)
        b = 7
        for i in range(5):
            b += 2
            pygame.draw.rect(surf, (0, 0, b), [-2, -2, self.info_canvas.get_width() - 60 + i, 300 + i], 1, 4)
        self.info_canvas.blit(surf, (32, y - 18))

        games = self.game.games[:]
        if not games:
            games.append(["???", "???"])

        score_canvas = pygame.Surface((self.info_canvas.get_width() - 60, 220), pygame.SRCALPHA)

        for i, game in enumerate(games):
            Label.render_text(score_canvas, str(game[self.__player % 2]),
                              ((score_canvas.get_width() + 5) // 4, self.score_y_offset + i * 25),
                              self.assets.font24, (180, 180, 180))
            Label.render_text(score_canvas, str(game[not self.__player % 2]),
                              ((3 * score_canvas.get_width() - 5) // 4, self.score_y_offset + i * 25),
                              self.assets.font24, (180, 180, 180))

        self.info_canvas.blit(score_canvas, (self.info_canvas.get_width() // 2 - score_canvas.get_width() // 2, y + 18))

        pygame.draw.line(self.info_canvas, (70, 110, 150), (35, 445), (self.info_canvas.get_width() - 35, 445))
        surf2 = pygame.Surface(self.info_canvas.get_size(), pygame.SRCALPHA)
        a = 255
        for i in range(35):
            a -= 7
            pygame.draw.rect(surf2, (0, 0, 20, a),
                             [36, 444 - i, self.info_canvas.get_width() - 71, 1])
        self.info_canvas.blit(surf2, (0, 0))

        final_score = self.game.get_final_game_score()
        Label.render_text(self.info_canvas, str(final_score[0]), ((self.info_canvas.get_width() + 70) // 4, 465),
                          self.assets.font24, (220, 220, 220))
        Label.render_text(self.info_canvas, str(final_score[1]), ((3 * self.info_canvas.get_width() - 70) // 4, 465),
                          self.assets.font24, (220, 220, 220))

    def render_game(self) -> None:
        self.canvas.blit(self.assets.table, (self.canvas.get_width() // 2 - self.assets.table.get_width() // 2,
                                             self.canvas.get_height() // 2 - self.assets.table.get_height() // 2))

        self.canvas.blit(self.timed_actions_before_canvas, (0, 0))

        self.render_players()
        self.render_hand()

        self.sort_cards_button.render()

        self.canvas.blit(self.timed_actions_after_canvas, (0, 0))

        if (
                self.game.get_current_game_state() is GameState.ZVANJE_ADUTA and
                self.game.get_adut() is None and
                self.game.player_turn == self.__player and
                not self.game.dalje[self.__player]
        ):
            self.render_calling_adut()

        if self.game.get_current_game_state() is GameState.ZVANJA:
            if not self.zvanja_dalje and not self.called_zvanje:
                self.render_zvanja()
            elif self.game.get_zvanje_state() == 1:
                self.render_game_zvanje()

    def render_calling_adut(self) -> None:
        surf = pygame.Surface(self.display.get_size(), pygame.SRCALPHA)
        surf.fill((0, 0, 0))
        surf.set_alpha(100)
        self.display.blit(surf, (0, 0))

        for button in self.call_adut_buttons:
            button.render()

        if self.game.count_dalje < 3:
            self.dalje_button.render()

    def render_zvanja(self) -> None:
        surf = pygame.Surface((self.display.get_width(), 140), pygame.SRCALPHA)
        surf.fill((0, 0, 0))
        surf.set_alpha(175)
        self.display.blit(surf, (0, self.display.get_height() // 2 - surf.get_height() // 2 - 30))

        self.zvanja_label.render()
        self.ima_zvanja_button.render()
        self.nema_zvanja_button.render()

    def render_game_zvanje(self, zvanja_gap: int = 20, card_width: int = 30) -> None:
        for player in range(4):
            if not self.game.final_zvanja[player]:
                continue
            rel_player = player
            if self.__player > 1:
                rel_player += 2
                if rel_player > 3:
                    rel_player -= 4

            zvanja = self.game.zvanja[player]
            zvanja_render_length = sum(len(z) * card_width for z in zvanja) + (len(zvanja) - 1) * zvanja_gap
            x, y = self.zvanja_card_positions[rel_player]
            x -= zvanja_render_length // 2

            for zvanje in zvanja:
                for card in zvanje:
                    card_img = self.assets.card_images[card]
                    if card not in self.zvanja_card_offsets:
                        self.zvanja_card_offsets[card] = random.randint(-2, 2), random.randint(-2, 2)
                    x_off, y_off = self.zvanja_card_offsets[card]
                    self.canvas.blit(
                        card_img, (x + x_off, y - card_img.get_height() // 2 + y_off)
                    )
                    x += card_width
                x += zvanja_gap

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
                x, y = self.player_positions[i + 1 if i < 3 else 0]
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
            if idx == self.game.diler:
                add_y = not int(idx < 2) if self.__player > 1 else int(idx < 2)
                if add_y == 0:
                    add_y = -1
                add_y *= 20
                Label.render_text(self.canvas, "[DILER]",
                                  (x, y + 70 * (not int(idx < 2) if self.__player > 1 else int(idx < 2)) - 35 + add_y),
                                  self.assets.font18, (220, 220, 220), bold=True)

    def render_hand(self) -> None:
        if self.game.get_current_game_state() is GameState.ZVANJE_ADUTA and not self.game.dalje[self.__player]:
            self.render_cards(self.game.get_netalon(self.__player))
        elif (
                self.game.get_current_game_state() is GameState.ZVANJA or
                self.game.dalje[self.__player] or
                self.game.get_current_game_state() is GameState.IGRA
        ):
            self.render_cards(self.get_cards().sve)

    def render_cards(self, cards: list) -> None:
        self.render_gained_cards()

        self.render_player_cards()

        self.render_cards_on_table()

        for i in self.switched_cards:
            card = cards[i]
            x = self.inventory[i].x
            y = self.inventory[i].y
            alpha = self.inventory[i].angle
            card = pygame.transform.rotate(self.assets.card_images[card], -82 - alpha)
            self.render_card_outline(card, x, y, self.switched_cards_marker_color)

        for i in self.selected_cards_for_bela:
            if i is not None:
                card = cards[i]
                x = self.inventory[i].x
                y = self.inventory[i].y
                alpha = self.inventory[i].angle
                card = pygame.transform.rotate(self.assets.card_images[card], -82 - alpha)
                self.render_card_outline(card, x, y, self.called_bela_marker_color)

        self.render_cards_in_hand(cards)

        if self.moving_card is not None:
            card = self.inventory[self.moving_card]
            self.canvas.blit(
                img := pygame.transform.rotate(self.assets.card_images[card.card], -82 - card.angle),
                (card.x - img.get_width() // 2, card.y - img.get_height() // 2)
            )

    def render_gained_cards(self) -> None:
        for i in range(4):
            rel_player = i
            if self.__player > 1:
                rel_player += 2
            if rel_player > 3:
                rel_player = rel_player - 4
            if self.game.stihovi[i]:
                x, y = self.gained_stihovi_positions[rel_player]
                card = pygame.transform.rotate(self.assets.card_back, self.gained_stihovi_angles[rel_player])
                self.canvas.blit(card, (x - card.get_width() // 2, y - card.get_height() // 2))

    def render_cards_in_hand(self, cards: list) -> None:
        for i, card in enumerate(cards):
            if i == self.moving_card or self.selected_cards[i]:
                continue
            if (
                    self.game.get_current_game_state() is GameState.ZVANJA and
                    self.game.get_zvanje_state() == 1 and
                    card in list(chain(*self.game.get_player_zvanja(self.__player)))
            ):
                continue
            x = self.inventory[i].x
            y = self.inventory[i].y
            alpha = self.inventory[i].angle
            card = pygame.transform.rotate(self.assets.card_images[card], -82 - alpha)
            if i in self.switched_cards:
                if abs(self.switched_cards[0] - self.switched_cards[1]) > 1:
                    self.render_card_outline(card, x, y, self.switched_cards_marker_color)
                elif i == min(self.switched_cards):
                    self.render_card_outline(card, x, y, self.switched_cards_marker_color)

            if i in self.selected_cards_for_bela:
                if abs(self.selected_cards_for_bela[0] - self.selected_cards_for_bela[1]) > 1:
                    self.render_card_outline(card, x, y, self.called_bela_marker_color)
                elif i == min(self.selected_cards_for_bela):
                    self.render_card_outline(card, x, y, self.called_bela_marker_color)
            self.canvas.blit(card, (x - card.get_width() // 2, y - card.get_height() // 2))

        for i, card in enumerate(cards):
            if i == self.moving_card or not self.selected_cards[i]:
                continue
            if (
                    self.game.get_current_game_state() is GameState.ZVANJA and
                    self.game.get_zvanje_state() == 1 and
                    card in list(chain(*self.game.get_player_zvanja(self.__player)))
            ):
                continue
            x = self.inventory[i].x
            y = self.inventory[i].y
            alpha = self.inventory[i].angle
            card = self.assets.card_images[card]
            card = pygame.transform.scale(
                card, (int(card.get_width() * 1.2), int(card.get_height() * 1.2))
            )
            card = pygame.transform.rotate(card, -82 - alpha)
            self.canvas.blit(card, (x - card.get_width() // 2, y - card.get_height() // 2))

    def render_cards_on_table(self) -> None:
        if self.game.turn_just_ended:
            for card in self.cards_on_table:
                if card is None:
                    continue
                card_img = pygame.transform.rotate(self.assets.card_images[card.card], -82 - card.angle)
                self.canvas.blit(card_img, (card.x - card_img.get_width() // 2, card.y - card_img.get_height() // 2))
            return

        for card in self.game.cards_on_table:
            if card is None:
                continue
            card_img = pygame.transform.rotate(self.assets.card_images[card.card], -82 - card.angle)
            if (
                    "DISPLAY_CARD_PLAYED" in self.timed_actions[0] and
                    card.card == self.timed_actions[0]["DISPLAY_CARD_PLAYED"][2].card
            ):
                action = self.timed_actions[0]["DISPLAY_CARD_PLAYED"]
                current_time = time.time() - action[1]
                if action[0] and current_time < 0.8:
                    rendering.render_outline(
                        card_img, self.canvas, self.placed_card_marker_color, card.x, card.y, 3, 3, 2
                    )
            self.canvas.blit(card_img, (card.x - card_img.get_width() // 2, card.y - card_img.get_height() // 2))

    def render_card_outline(self, card: pygame.Surface, x: int, y: int, color: Tuple[int, int, int, int]) -> None:
        rendering.render_outline(card, self.canvas, color, x, y, 3, 3, 2)

    def render_player_cards(self) -> None:
        self.render_players_cards_in_talon()
        self.render_players_cards_in_hand()

    def render_players_cards_in_talon(self) -> None:
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

    def render_players_cards_in_hand(self, k: int = 15, r: int = 100) -> None:
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

            # p -= self.__player
            # if p <= 0:
            #    p = 4 - p

            cards = self.game.get_netalon(p) if self.game.get_current_game_state() is GameState.ZVANJE_ADUTA else \
                self.game.cards[p].sve
            alpha = (98 if rot else -82) - len(cards) * k // 2
            for card in cards:
                if (
                        self.game.get_current_game_state() is GameState.ZVANJA and
                        self.game.get_zvanje_state() == 1 and
                        card in list(chain(*self.game.get_player_zvanja(p)))
                ):
                    continue
                x = int(math.cos(math.radians(alpha)) * r)
                y = int(math.sin(math.radians(alpha)) * r)
                alpha += k
                card = pygame.transform.rotate(self.assets.card_back, (98 if rot else -82) - alpha)
                self.canvas.blit(card, (x0 + x - card.get_width() // 2, y0 + y - card.get_height() // 2))

    def render_timed_actions(self) -> None:
        self.timed_actions_before_canvas = pygame.Surface(self.canvas.get_size(), pygame.SRCALPHA)
        self.timed_actions_after_canvas = pygame.Surface(self.canvas.get_size(), pygame.SRCALPHA)

        to_remove = []

        for action, args in self.timed_actions[1].items():
            t = time.time()

            if action == "DISPLAY_CARD_ERROR" and args[0] and t - args[1] < 0.4:
                self.display_card_error(t - args[1])

            if action == "GAME_OVER" and args[0]:
                if t - args[1] < 8:
                    self.display_game_over(t - args[1])
                else:
                    self.end_game = True
                    to_remove.append("GAME_OVER")

        for k in to_remove:
            self.timed_actions[1].pop(k)

    def end_current_game(self) -> None:
        self.data = self.network.send(Commands.END_GAME)

        self.cards_on_table_positions_p1 = []
        self.cards_on_table_positions_p2 = []

        self.inventory = []
        self.inventory_calculated = False

        self.cards_on_table = []
        self.switched_cards = []
        self.moving_card = None
        self.selected_cards = [False for _ in range(8)]
        self.selected_cards_for_bela = [None, None]

        self.adut_dalje = False
        self.zvanja_dalje = False
        self.called_zvanje = False
        self.zvanja_timer_created = False
        self.calling_bela = False

        self.activated_turn_end = False
        self.activated_game_over = False
        self.end_game = False

        self.last_frame_cards_on_table = []

        self.sort_cards_button.reinit()
        self.nema_zvanja_button.reinit()
        self.ima_zvanja_button.reinit()
        self.dalje_button.reinit()
        for btn in self.call_adut_buttons:
            btn.reinit()

    def calculate_card_positions(self, cards: list, r: int = 100, k: int = 15) -> None:
        self.inventory = []
        x0, y0 = self.card_positions[self.__player % 2]
        alpha = -82 - len(cards) * k // 2
        for card in cards:
            x = math.cos(math.radians(alpha)) * r
            y = math.sin(math.radians(alpha)) * r
            alpha += k
            self.inventory.append(
                Card(card, int(x0 + x), int(y0 + y), alpha, RotatingRect(int(x0 + x), int(y0 + y),
                                                                         self.assets.card_width,
                                                                         self.assets.card_height,
                                                                         100 - alpha
                                                                         ))
            )
        self.inventory_calculated = True

    def sync_inventory(self) -> None:
        org_cards = self.get_cards().sve
        if self.game.get_current_game_state() is GameState.ZVANJE_ADUTA and not self.adut_dalje:
            org_cards = self.get_cards().netalon

        inv_cards = list(map(lambda x: x.card, self.inventory))

        diff = list(set(inv_cards).difference(set(org_cards)))
        diff2 = list(set(org_cards).difference(set(inv_cards)))

        for i, inv_card in enumerate(self.inventory):
            if inv_card.card in diff:
                self.inventory[i].card = diff2.pop()

    def recheck_zvanja(self) -> None:
        for i, v in enumerate(self.selected_cards):
            self.selected_cards[i] = False

    def calculate_card_removal_paths_p1(self, gap: int = 8, interval: float = 0.5) -> None:
        if self.cards_on_table_positions_p1:
            return

        for i, card in enumerate(self.cards_on_table):
            new_x = self.canvas.get_width() // 2 + i * (gap + self.assets.card_width) - \
                    (gap * 3 / 2 + self.assets.card_width * 3 / 2)
            new_y = self.canvas.get_height() // 2

            dist_x = new_x - card.x
            dist_y = new_y - card.y
            dist_angle = (card.angle + 82)
            if card.angle < 82:
                dist_angle *= -1

            vel_x = dist_x / interval
            vel_y = dist_y / interval
            vel_angle = dist_angle / interval

            card_x = card.x
            card_y = card.y
            angle = card.angle

            n = 10
            path = []
            for j in range(1, n):
                card_x += vel_x * interval / n
                card_y += vel_y * interval / n
                angle += vel_angle * interval / n
                path.append([interval / n * j, int(card_x), int(card_y), int(angle)])
            path.append([interval, new_x, new_y, -82])

            self.cards_on_table_positions_p1.append(path)

    def calculate_card_removal_paths_p2(self, interval: float = 0.5) -> None:
        if self.cards_on_table_positions_p2:
            return

        rel_turn = self.game.current_turn_winner
        if self.__player > 1:
            rel_turn -= 2

        new_x, new_y = self.gained_stihovi_positions[rel_turn]
        new_angle = self.gained_stihovi_angles[rel_turn]

        for i, card in enumerate(self.cards_on_table):
            dist_x = new_x - card.x
            dist_y = new_y - card.y
            dist_angle = card.angle - new_angle
            if card.angle < -new_angle:
                dist_angle *= -1

            vel_x = dist_x / interval
            vel_y = dist_y / interval
            vel_angle = dist_angle / interval

            card_x = card.x
            card_y = card.y
            angle = card.angle

            n = 10
            path = []
            for j in range(1, n):
                card_x += vel_x * interval / n
                card_y += vel_y * interval / n
                angle += vel_angle * interval / n
                path.append([interval / n * j, int(card_x), int(card_y), int(angle)])
            path.append([interval, new_x, new_y, new_angle])

            self.cards_on_table_positions_p2.append(path)

    def finish_zvanja(self, _) -> None:
        self.data = self.network.send(Commands.ZVANJE_GOTOVO)

    # Timed action functions

    def display_card_error(self, current_time: float) -> None:
        value = 0.2 - abs(current_time - 0.2)
        alpha = value * 500

        rect = pygame.Rect(self.canvas.get_width() // 2 - 60, self.canvas.get_height() // 2 - 60, 120, 120)
        surf = pygame.Surface((120, 120), pygame.SRCALPHA)
        pygame.draw.rect(surf, (255, 0, 0, alpha), (0, 0, 120, 120), 0, 4)
        self.timed_actions_before_canvas.blit(surf, rect)

    def display_game_over(self, current_time: float) -> None:
        value = 4 - abs(current_time - 4)
        alpha = max(min(int(value * 800), 255), 0)

        surf = pygame.Surface(self.canvas.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(surf, (0, 0, 0, 150), self.canvas.get_rect())

        Label.render_text(
            surf,
            "GAME OVER",
            (self.canvas.get_width() // 2, self.canvas.get_height() // 2 - 100),
            self.assets.font48,
            (255, 255, 255),
            bold=True
        )

        str_team1 = self.game.player_data[0]["nickname"] + " & " + self.game.player_data[2]["nickname"]
        str_team2 = self.game.player_data[1]["nickname"] + " & " + self.game.player_data[3]["nickname"]
        k1 = len(str_team2) - len(str_team1)
        k2 = -k1
        Label.render_text(
            surf,
            " " * max(k1, 0) + str_team1 + "  -  " + str_team2 + " " * max(k2, 0),
            (self.canvas.get_width() // 2, self.canvas.get_height() // 2),
            self.assets.font24,
            (200, 200, 200)
        )
        str_p1 = str(self.game.points[0])
        str_p2 = str(self.game.points[1])
        k1 = len(str_p2) - len(str_p1)
        k2 = -k1
        Label.render_text(
            surf,
            " " * max(k1, 0) + str_p1 + "  -  " + str_p2 + " " * max(k2, 0),
            (self.canvas.get_width() // 2, self.canvas.get_height() // 2 + 40),
            self.assets.font24,
            (200, 200, 200)
        )

        surf.set_alpha(alpha)

        self.timed_actions_after_canvas.blit(surf, (0, 0))

    def switch_card_unmark(self, current_time: float) -> None:
        value = 0.5 - abs(current_time - 0.5)
        alpha = int(value * 300)
        self.switched_cards_marker_color = (0, 255, 0, max(min(255, alpha), 0))

    def placed_card_unmark(self, current_time: float) -> None:
        value = 0.4 - abs(current_time - 0.4)
        alpha = int(value * 300)
        self.placed_card_marker_color = (0, 0, 255, max(min(255, alpha), 0))

    def called_bela_unmark(self, current_time: float) -> None:
        value = 0.5 - abs(current_time - 0.5)
        alpha = int(value * 300)
        self.called_bela_marker_color = (255, 0, 0, max(min(255, alpha), 0))

    def move_removed_cards(self, current_time: float) -> None:
        if not self.cards_on_table_positions_p1:
            self.calculate_card_removal_paths_p1()
        if not self.cards_on_table_positions_p2 and self.cards_on_table_positions_p1:
            self.calculate_card_removal_paths_p2()

        if current_time < 1:
            for i, positions in enumerate(self.cards_on_table_positions_p1):
                for pos in positions:
                    if pos[0] < current_time:
                        self.cards_on_table[i].x = pos[1]
                        self.cards_on_table[i].y = pos[2]
                        self.cards_on_table[i].angle = pos[3]
        else:
            for i, positions in enumerate(self.cards_on_table_positions_p2):
                for j, pos in enumerate(positions):
                    if pos[0] < current_time - 1:
                        self.cards_on_table[i].x = pos[1]
                        self.cards_on_table[i].y = pos[2]
                        self.cards_on_table[i].angle = pos[3]
                        if j == len(positions) - 1:
                            self.timed_actions[0]["TURN_ENDED"][1] -= 2

    def move_back_card(self, current_time: float, card: int, copy_card: Card) -> None:
        card_x, card_y = copy_card.get_pos()
        org_x, org_y = copy_card.def_pos

        vel = [org_x - card_x, org_y - card_y]
        dist = math.sqrt((org_x - card_x) ** 2 + (org_y - card_y) ** 2)

        self.inventory[card].x += vel[0] * min(max(abs(dist), 50), 60) / 1000
        self.inventory[card].y += vel[1] * min(max(abs(dist), 50), 60) / 1000

        self.timed_actions[0]["MOVE_BACK_CARD"] = [True, time.time(), card, copy_card]

        if (
                math.sqrt((org_x - self.inventory[card].x) ** 2 + (org_y - self.inventory[card].y) ** 2) <= 10 or
                (self.inventory[card].y > org_y and vel[1] > 0) or
                (self.inventory[card].y < org_y and vel[1] < 0) or
                (self.inventory[card].x > org_x and vel[0] > 0) or
                (self.inventory[card].x < org_x and vel[0] < 0)
        ):
            self.inventory[card].move_back()
            self.timed_actions[0]["MOVE_BACK_CARD"] = [False, 0, card, copy_card]

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
