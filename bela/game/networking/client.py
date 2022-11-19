import copy
import math
import random
import time
from typing import Any

import pygame

from bela.game.main.bela import GameState, Hand, Card
from bela.game.networking.commands import Commands
from bela.game.ui.button import Button
from bela.game.ui.container import Container
from bela.game.ui.grid import Grid
from bela.game.ui.input_field import InputField
from bela.game.ui.padding import Padding
from bela.game.utils.animations import AnimationHandler, AnimationFactory
from bela.game.utils.assets import Assets
from bela.game.utils.gamestates import ClientGameStates
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

        self.win = pygame.display.set_mode(config.WINDOW_SIZE, pygame.SRCALPHA)
        pygame.display.set_caption(f"Bela")

        self.canvas = pygame.Surface(config.CANVAS_SIZE, pygame.SRCALPHA)
        self.info_canvas = pygame.Surface(config.INFO_CANVAS_SIZE, pygame.SRCALPHA)
        self.match_over_menu_canvas = pygame.Surface(config.CANVAS_SIZE, pygame.SRCALPHA)

        self.timed_actions_before_canvas = pygame.Surface(self.canvas.get_size(), pygame.SRCALPHA)
        self.timed_actions_after_canvas = pygame.Surface(self.canvas.get_size(), pygame.SRCALPHA)

        # Event Handler

        self.event_handler = EventHandler()

        # Assets

        self.assets = Assets()

        # Animations

        self.animation_handler = AnimationHandler()

        # Variables

        self.clock = pygame.time.Clock()
        self.__fps = 60

        self.data: dict[str, Any] = {"game": None}

        self.__player = 0
        self.__client_id = 0

        self.game_state: ClientGameStates = ClientGameStates.MAIN_MENU

        self.background_color = (0, 0, 20)

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
        self.shown_zvanja_points = False
        self.calling_bela = False
        self.bela_just_called = False

        self.switched_cards = []
        self.switched_cards_marker_color = (0, 255, 0, 0)
        self.placed_card_marker_color = (0, 0, 255, 0)
        self.called_bela_marker_color = (255, 0, 0, 0)

        self.activated_turn_end = False
        self.activated_game_over = False
        self.activated_match_over = False
        self.ended_game = False
        self.end_game = False
        self.end_match = False

        self.score_y_offset = 15

        self.last_frame_cards_on_table = []

        self.timed_actions = [{}, {}]
        self.timed_actions_durations = {
            "MOVE_BACK_CARD": 1.0,
            "SWITCH_CARDS": 1.0,
            "DISPLAY_CARD_PLAYED": 0.8,
            "CALL_BELA": 1.0,
            "TURN_ENDED": 2.0,
            "DISPLAY_CARD_ERROR": 0.4,
            "GAME_OVER": 8.0,
            "MATCH_OVER": 8.0,
            "BELOT": 5.0
        }
        self.attributes = {
            "__render_zvanja_gap": 20,
            "__render_zvanja_card_width": 30,
            "__render_score_y_value": 200,
            "__render_calling_adut_bg_alpha": 100,
            "__render_zvanja_bg_alpha": 175,
            "__var_waiting_dots_timer": 0.8,
            "__var_waiting_dots_count_max": 3,
            "__var_title_font_size": 210,
            "__var_waiting_label_font_size": 100,
            "__var_zvanja_points_appear_duration": 2,
            "__var_belot_text_animation_stop_point": 300,
            "__var_bela_appearing_text_duration": 1.7,
            "__var_zvanje_showing_duration": 4,
            "__var_scroll_value": 10,
            "__var_info_canvas_line_color": (70, 110, 150),
            "__var_info_canvas_text_color": (255, 255, 255),
            "__var_info_canvas_dark_text_color": (200, 200, 200),
            "__var_info_canvas_score_color": (180, 180, 180),
            "__var_info_canvas_final_score_color": (220, 220, 220),
            "__var_match_over_menu_color": (0, 0, 30)
        }

        # Event functions

        def on_play_btn_click(cls, x, y):
            cls.connect()

        def on_options_btn_click(cls, x, y):
            pass

        def on_create_new_game_btn_click(cls, x, y):
            cls.animation_handler.add_animation(
                AnimationFactory.create_sliding_screen_animation(800, 390, "up", vel=40),
                id_="#CREATE_NEW_GAME"
            )
            cls.update_lobby_new_game_container()

        def on_sort_cards_btn_click(cls, x, y):
            cls.data = cls.network.send(Commands.SORT_CARDS)
            if cls.game.get_current_game_state() == GameState.ZVANJE_ADUTA and not cls.game.dalje[cls.__player]:
                cls.calculate_card_positions(cls.game.get_netalon(cls.get_player()))
            else:
                cls.calculate_card_positions(cls.get_cards().sve)

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

        def on_menu_return_btn_click(cls, x, y):
            pass

        def on_play_again_btn_click(cls, x, y):
            pass

        # Timers

        self.timer_handler = TimerHandler()

        # GUI Elements

        self.title = Label(
            self.canvas,
            (520, 180),
            (300, 200),
            pygame.font.SysFont("consolas", self.attributes["__var_title_font_size"]),
            text="BELA",
            font_color=Colors.white,
            bold=True
        )

        self.play_btn = Button(
            self.canvas,
            (20, 530),
            (400, 70),
            self.assets.font32,
            center_x=False,
            text="IGRAJ",
            color=Colors.black,
            font_color=Colors.white,
            bold=True,
            text_orientation="left",
            padding=10
        ).set_on_click_listener(on_play_btn_click, self)

        self.options_btn = Button(
            self.canvas,
            (20, 450),
            (400, 70),
            self.assets.font32,
            center_x=False,
            text="OPCIJE",
            color=Colors.black,
            font_color=Colors.white,
            bold=True,
            text_orientation="left",
            padding=10
        ).set_on_click_listener(on_options_btn_click, self)

        self.create_new_game_button = Button(
            self.canvas,
            (self.canvas.get_width() // 2, 550),
            (400, 35),
            self.assets.font24,
            text="NOVA IGRA",
            color=Color(180, 150, 0),
            font_color=Colors.white,
            bold=True,
            border_radius=10
        ).set_on_click_listener(on_create_new_game_btn_click, self)

        self.nickname_input_field = InputField(
            self.canvas,
            (self.canvas.get_width() // 2, 40),
            (250, 40),
            self.assets.font24,
            hint="Player",
            color=Color(100, 100, 100, 30),
            font_color=Colors.white,
            bold=True,
            padding=10,
            border_color=Color(200, 200, 200),
            border_radius=10,
            border_width=1,
            max_length=8,
            text_underline=True
        )

        self.lobby_game_containers = [
            Container(
                self.canvas, ((self.canvas.get_width() - 4 * 180 + 30) // 2 + 75 + j * 180, 170 + i * 190), (150, 170),
                Color(0, 0, 20), border_color=Color(40, 40, 60), border_radius=8, border_width=1, active=False
            ) for j in range(4) for i in range(2)
        ]

        self.lobby_new_game_container = Container(
            self.canvas,
            (self.canvas.get_width() // 2, self.canvas.get_height() + 250),
            (400, 500),
            Color(160, 130, 0),
            border_radius=30
        )

        self.sort_cards_button = Button(
            self.canvas,
            (120, 550),
            (160, 30),
            self.assets.font18,
            text="SORTIRAJ KARTE",
            font_color=Colors.white,
            bold=True
        ).set_on_click_listener(on_sort_cards_btn_click, self)

        types = ["karo", "pik", "herc", "tref"]
        self.call_adut_buttons = [
            Button(
                self.canvas,
                (self.canvas.get_width() // 2 + int(100 * (0.5 - i)), self.canvas.get_height() // 2),
                (50, 50),
                self.assets.font18,
                text=types[i + 1],
                font_color=Colors.white,
                bold=True
            ).set_on_click_listener(on_adut_btn_click, self, pass_self=True) for i in range(-1, 3)
        ]

        self.dalje_button = Button(
            self.canvas,
            (self.canvas.get_width() // 2, self.canvas.get_height() // 2 + 70),
            (70, 36),
            self.assets.font18,
            text="DALJE",
            font_color=Colors.white,
            bold=True
        ).set_on_click_listener(on_dalje_btn_click, self)

        self.nema_zvanja_button = Button(
            self.canvas,
            (self.canvas.get_width() // 2 - 100, self.canvas.get_height() // 2),
            (140, 30),
            self.assets.font18,
            text="NEMAM ZVANJA",
            font_color=Colors.white,
            bold=True
        ).set_on_click_listener(on_nema_zvanja_btn_click, self)

        self.ima_zvanja_button = Button(
            self.canvas,
            (self.canvas.get_width() // 2 + 100, self.canvas.get_height() // 2),
            (140, 30),
            self.assets.font18,
            text="ZOVEM",
            font_color=Colors.white,
            bold=True
        ).set_on_click_listener(on_ima_zvanja_btn_click, self)

        self.zvanja_label = Label(
            self.canvas,
            (self.canvas.get_width() // 2, self.canvas.get_height() // 2 - 60),
            (400, 100),
            self.assets.font32,
            text="OZNAČITE ZVANJA",
            font_color=Colors.white,
            bold=True
        )

        self.game_over_label = Label(
            self.canvas,
            (self.canvas.get_width() // 2, self.canvas.get_height() // 2 - 20),
            (500, 200),
            self.assets.font48,
            text="RUNDA GOTOVA",
            font_color=Colors.white,
            bold=True
        )

        self.game_over_label2 = Label(
            self.canvas,
            (self.canvas.get_width() // 2, self.canvas.get_height() // 2 + 40),
            (600, 300),
            self.assets.font24,
            font_color=Color(200, 200, 200),
            bold=True
        )

        self.belot_label = Label(
            self.canvas,
            (self.canvas.get_width() // 2, self.canvas.get_height() // 2 - 20),
            (500, 200),
            self.assets.font48,
            text="BELOT",
            font_color=Colors.white,
            bold=True
        )

        self.match_over_label = Label(
            self.canvas,
            (self.canvas.get_width() // 2, -300),
            (500, 200),
            self.assets.font64,
            text="IGRA GOTOVA",
            font_color=Colors.white,
            bold=True
        )

        self.match_over_menu_title = Label(
            self.match_over_menu_canvas,
            (self.canvas.get_width() // 2, 200),
            (500, 200),
            self.assets.font64,
            text="IGRA ZAVRŠENA",
            font_color=Colors.white,
            bold=True
        )

        self.menu_return_button = Button(
            self.match_over_menu_canvas,
            (self.canvas.get_width() // 2, 375),
            (300, 50),
            self.assets.font32,
            text="MAIN MENU",
            font_color=Colors.white.darker(60),
            bold=True,
            color=Color(150, 150, 150, 60),
            border_radius=10,
            border_color=Color(150, 150, 150)
        ).set_on_click_listener(on_menu_return_btn_click, self)

        self.menu_play_again_button = Button(
            self.match_over_menu_canvas,
            (self.canvas.get_width() // 2, 450),
            (300, 50),
            self.assets.font32,
            text="IGRAJ PONOVO",
            font_color=Colors.white.darker(60),
            bold=True,
            color=Color(150, 150, 150, 60),
            border_radius=10,
            border_color=Color(150, 150, 150)
        ).set_on_click_listener(on_play_again_btn_click, self)

        """-----------------------------------MAIN LOOP---------------------------------"""
        while True:

            self.update()
            self.render()

            if not self.event_handler.loop():
                break

        pygame.quit()

    def connect(self) -> None:
        self.network.connect()
        self.network.update_connection()
        self.__client_id = self.network.client_id

    def update(self):
        if self.game_state not in (ClientGameStates.MAIN_MENU, ClientGameStates.UNDEFINED):
            self.data = self.network.send(Commands.GET)

        self.timer_handler.update()

        self.animation_handler.update()

        self.update_timed_actions()

        self.update_game_states()

        if self.game_state is ClientGameStates.GAME:
            self.update_game()
        elif self.game_state is ClientGameStates.LOBBY:
            self.update_lobby()
        elif self.game_state is ClientGameStates.MAIN_MENU:
            self.update_menu()
        elif self.game_state is ClientGameStates.MATCH_OVER_MENU:
            self.update_match_over_menu()

    def update_game_states(self) -> None:
        #self.game_state = ClientGameStates.MATCH_OVER_MENU

        if self.play_btn.is_clicked:
            self.game_state = ClientGameStates.LOBBY
        if (
            self.animation_handler.has("#MATCH_OVER_SCREEN_FALL") and
            self.animation_handler.get_animation("#MATCH_OVER_SCREEN_FALL").is_finished()
        ):
            self.animation_handler.remove_animation("#MATCH_OVER_SCREEN_FALL")
            if "MATCH_OVER" in self.timed_actions[1]:
                self.timed_actions[1].pop("MATCH_OVER")
            self.game_state = ClientGameStates.MATCH_OVER_MENU

    def update_menu(self) -> None:
        self.play_btn.update(self.event_handler)
        self.options_btn.update(self.event_handler)

    def update_lobby(self) -> None:
        if self.animation_handler.has("#CREATE_NEW_GAME"):
            self.lobby_new_game_container.move(
                y=self.animation_handler.get_animation("#CREATE_NEW_GAME").get_current_data()
            )
            self.lobby_new_game_container.update(self.event_handler)
        else:
            self.create_new_game_button.update(self.event_handler)
            self.nickname_input_field.update(self.event_handler)

            for container in self.lobby_game_containers:
                if container.active:
                    container.update(self.event_handler)

    def update_lobby_new_game_container(self) -> None:
        self.lobby_new_game_container.add_element(
            Label(
                self.canvas,
                (0, 0),
                (200, 50),
                self.assets.font24,
                text="NAPRAVI NOVU IGRU",
                font_color=Colors.white,
                bold=True
            ),
            id_="#TITLE",
            pad_y=20
        ).add_element(
            Padding(
                self.canvas,
                (0, 0),
                (0, 40)
            )
        ).add_element(
            InputField(
                self.canvas,
                (0, 0),
                (200, 30),
                self.assets.font24,
                hint="Game_0",  # TODO: replace with the current game count
                color=Color(100, 100, 100, 100),
                font_color=Colors.white,
                bold=True,
                padding=10,
                border_color=Color(200, 200, 200),
                border_radius=10,
                border_width=1,
                max_length=8,
                text_underline=True
            ),
            id_="#GAME_NAME",
            pad_y=10
        ).add_element(
            InputField(
                self.canvas,
                (0, 0),
                (200, 30),
                self.assets.font24,
                hint="1001",
                color=Color(100, 100, 100, 100),
                font_color=Colors.white,
                bold=True,
                padding=10,
                border_color=Color(200, 200, 200),
                border_radius=10,
                border_width=1,
                max_length=8,
                text_underline=True,
                char_set="0123456789"
            ),
            id_="#GAME_POINTS",
            pad_y=10
        ).add_element(
            Grid(
                self.canvas,
                (0, 0),
                ("fit", "fit"),
                (3, 2),
                render_col_splitter=True,
            ).add_element(
                InputField(
                    self.canvas,
                    (0, 0),
                    (150, 50),
                    self.assets.font24,
                    hint="Team Blue",
                    font_color=Color(0, 0, 200),
                    bold=True,
                    border_radius=0,
                    max_length=9,
                    text_underline=True,
                    text_underline_color=Color(0, 0, 200),
                    text_orientation="center"
                ), 0, 0
            ).add_element(
                InputField(
                    self.canvas,
                    (0, 0),
                    (150, 50),
                    self.assets.font24,
                    hint="Team Red",
                    font_color=Color(200, 0, 0),
                    bold=True,
                    border_radius=0,
                    max_length=9,
                    text_underline=True,
                    text_underline_color=Color(200, 0, 0),
                    text_orientation="center"
                ), 0, 1
            ).add_element(
                Container(
                    self.canvas,
                    (0, 0),
                    (200, 80),
                    Color(0, 0, 0, 0)
                ).add_element(
                    Padding(
                        self.canvas,
                        (0, 0),
                        (0, 25)
                    )
                ).add_element(
                    Label(
                        self.canvas,
                        (0, 0),
                        (200, 25),
                        self.assets.font24,
                        text=self.nickname_input_field.get_text(),
                        font_color=Color(230, 230, 230),
                        bold=True,
                        fit_size_to_text=False
                    )
                ).add_element(
                    Label(
                        self.canvas,
                        (0, 0),
                        (200, 10),
                        self.assets.font14,
                        text="ADMIN",
                        font_color=Color(200, 200, 200),
                        bold=True,
                        fit_size_to_text=False
                    )
                ), 1, 0
            ).add_element(
                Label(
                    self.canvas,
                    (0, 0),
                    (200, 50),
                    self.assets.font24,
                    text="IGRAČ 2",
                    font_color=Color(200, 200, 200),
                    bold=True
                ), 1, 1
            ).add_element(
                Label(
                    self.canvas,
                    (0, 0),
                    (200, 50),
                    self.assets.font24,
                    text="IGRAČ 3",
                    font_color=Color(200, 200, 200),
                    bold=True
                ), 2, 0
            ).add_element(
                Label(
                    self.canvas,
                    (0, 0),
                    (200, 50),
                    self.assets.font24,
                    text="IGRAČ 4",
                    font_color=Color(200, 200, 200),
                    bold=True
                ), 2, 1
            ),
            id_="#TEAM_GRID",
            pad_y=35,
            pad_x=10,
            fit_x=True,
            fit_y=True
        )

    def update_match_over_menu(self) -> None:
        self.menu_return_button.update(self.event_handler)
        self.menu_play_again_button.update(self.event_handler)

    def update_game(self) -> None:
        if self.game.current_game_over and not self.activated_game_over:
            self.timed_actions[1]["GAME_OVER"] = [True, self.timed_actions_durations["GAME_OVER"], time.time()]
            self.activated_game_over = True

        if self.game.current_match_over and not self.activated_match_over and not self.game.called_belot:
            self.timed_actions[1]["MATCH_OVER"] = [True, self.timed_actions_durations["MATCH_OVER"],
                                                   "GAME", time.time()]
            self.activated_match_over = True

        if self.end_game:
            self.end_current_game()

        if self.end_match:
            self.end_current_match()

        if not self.game.current_game_over:
            self.activated_game_over = False
            if not self.started_new_game:
                self.start_new_game()

        if self.game.called_bela and not self.bela_just_called:
            self.bela_just_called = True
            self.add_appearing_text((self.canvas.get_width() // 2, 170), "BELA", (0, 0, 100),
                                    self.attributes["__var_bela_appearing_text_duration"])
            self.add_appearing_text((self.canvas.get_width() // 2, 200), "+20", (0, 0, 100),
                                    self.attributes["__var_bela_appearing_text_duration"], font=self.assets.font32)

        if self.game.get_current_game_state() is GameState.ZVANJE_ADUTA and (
                self.game.get_adut() is None
                and self.game.player_turn == self.__player
                and not self.game.dalje[self.__player]
        ):
            self.update_calling_adut()

        if self.game.get_current_game_state() is GameState.ZVANJA and len(self.inventory) in (0, 6):
            self.calculate_card_positions(self.get_cards().sve)

        if not self.inventory_calculated:
            self.calculate_card_positions(self.game.get_netalon(self.__player))

        self.sync_inventory()

        self.update_score()

        self.update_cards()

        if self.game.get_current_game_state() is GameState.ZVANJA:
            if not self.zvanja_dalje and not self.called_zvanje:
                self.update_zvanja()
            elif self.game.get_zvanje_state() == 1:
                if not self.zvanja_timer_created:
                    countdown = self.attributes["__var_zvanje_showing_duration"]
                    if not any(self.game.zvanja):
                        countdown = 0
                    self.timer_handler.add_timer_during_exec("SHOW_ZVANJA", countdown, self.finish_zvanja, self)
                    self.zvanja_timer_created = True
                self.update_game_zvanje()

        self.sort_cards_button.update(self.event_handler)

    def update_score(self) -> None:
        if not pygame.Rect(self.canvas.get_width() + 35, 210,
                           self.info_canvas.get_width() - 70, 240).collidepoint(self.event_handler.get_pos()):
            return

        if self.event_handler.scrolls["up"]:
            self.score_y_offset = min(self.score_y_offset + self.attributes["__var_scroll_value"], 15)
        elif self.event_handler.scrolls["down"]:
            self.score_y_offset = max(self.score_y_offset - self.attributes["__var_scroll_value"],
                                      15 - (max(len(self.game.games), 5) - 5) * 25)

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

    def update_cards(self) -> None:
        self.update_cards_in_inventory()

        if self.game.turn_just_ended and not self.activated_turn_end:
            self.timed_actions[0]["TURN_ENDED"] = [True, self.timed_actions_durations["TURN_ENDED"], time.time()]
            self.cards_on_table = copy.deepcopy(self.game.cards_on_table)
            self.activated_turn_end = True

        if (
                len(self.game.cards_on_table) != len(self.last_frame_cards_on_table)
                and self.game.cards_on_table
        ):
            self.timed_actions[0]["DISPLAY_CARD_PLAYED"] = [True, self.timed_actions_durations["DISPLAY_CARD_PLAYED"],
                                                            time.time(), self.game.cards_on_table[-1]]

        # <DEBUG CODE>

        if self.on_turn() and self.game.get_current_game_state() is GameState.IGRA \
                and self.game.auto_play[self.__player]:
            data = {}
            i = -1
            for i, card in enumerate(self.inventory):
                data = self.network.send(Commands.new(Commands.PLAY_CARD, card))
                self.data = data
                if data["data"]["passed"]:
                    break
            if self.inventory and data["data"]["passed"]:
                self.inventory.pop(i)

        # </DEBUG CODE>

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
                    self.game.card_in_player_zvanja(card.card, self.__player)
            ):
                continue

            index = len(self.inventory) - i - 1

            if (
                    self.event_handler.presses["right"] and
                    card.rect.collidepoint(self.event_handler.get_pos()) and
                    self.game.get_current_game_state() is GameState.IGRA and
                    self.on_turn() and self.moving_card is None and
                    card.card in [("baba", self.game.get_adut()), ("kralj", self.game.get_adut())] and
                    self.game.player_has_bela(self.__player)
            ):
                self.call_bela()
                break

            if (
                    self.event_handler.held["left"] and
                    card.rect.collidepoint(self.event_handler.get_pos()) and
                    self.moving_card is None and
                    ("MOVE_BACK_CARD" not in self.timed_actions[0] or
                     not self.timed_actions[0]["MOVE_BACK_CARD"][0])
            ):
                self.moving_card = index

            if self.moving_card == index:
                self.inventory[index].set_pos(self.event_handler.get_pos())

    def handle_card_playing(self) -> None:
        data = self.network.send(Commands.new(Commands.PLAY_CARD, self.inventory[self.moving_card]))
        card_passed = data["data"]["passed"]
        self.data = data
        if card_passed:
            if self.calling_bela and None not in self.selected_cards_for_bela and \
                    self.inventory[self.moving_card].card in (("baba", self.game.get_adut()),
                                                              ("kralj", self.game.get_adut())):
                self.data = self.network.send(Commands.CALLED_BELA)
            self.calling_bela = False
            self.selected_cards_for_bela = [None, None]
            self.inventory.pop(self.moving_card)
            if self.game.cards_on_table:
                self.timed_actions[0]["DISPLAY_CARD_PLAYED"] = [True,
                                                                self.timed_actions_durations["DISPLAY_CARD_PLAYED"],
                                                                time.time(), self.game.cards_on_table[-1]]
        else:
            self.timed_actions[0]["MOVE_BACK_CARD"] = [True, self.timed_actions_durations["MOVE_BACK_CARD"],
                                                       time.time(),
                                                       self.moving_card,
                                                       copy.deepcopy(self.inventory[self.moving_card])]
            self.timed_actions[1]["DISPLAY_CARD_ERROR"] = [True, self.timed_actions_durations["DISPLAY_CARD_ERROR"],
                                                           time.time()]

    def handle_card_swapping(self) -> None:
        for i, card in enumerate(self.inventory):
            if (
                    self.game.get_current_game_state() is GameState.ZVANJA and
                    self.game.get_zvanje_state() == 1 and
                    self.game.card_in_player_zvanja(card.card, self.__player)
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
                self.timed_actions[0]["SWITCH_CARDS"] = [True, self.timed_actions_durations["SWITCH_CARDS"],
                                                         time.time()]
                break
        else:
            self.timed_actions[0]["MOVE_BACK_CARD"] = [True, self.timed_actions_durations["MOVE_BACK_CARD"],
                                                       time.time(),
                                                       self.moving_card,
                                                       copy.deepcopy(self.inventory[self.moving_card])]

    def update_timed_actions(self) -> None:
        to_remove = []
        for action, args in self.timed_actions[0].items():
            t = time.time()
            duration = args[1]

            if action == "MOVE_BACK_CARD" and args[0] and t - args[2] < duration:
                self.move_back_card(t - args[2], args[3], args[4])

            if action == "SWITCH_CARDS" and args[0]:
                if t - args[2] < duration:
                    self.switch_card_unmark(t - args[2])
                elif t - args[2] > duration:
                    self.switched_cards = []
                    to_remove.append("SWITCH_CARDS")

            if action == "DISPLAY_CARD_PLAYED" and args[0]:
                if t - args[2] < duration:
                    self.placed_card_unmark(t - args[2])
                elif t - args[2] > duration:
                    to_remove.append("DISPLAY_CARD_PLAYED")

            if action == "CALL_BELA" and args[0]:
                if t - args[2] < duration:
                    self.called_bela_unmark(t - args[2])
                elif t - args[2] > duration:
                    to_remove.append("CALL_BELA")

            if action == "TURN_ENDED" and args[0]:
                if t - args[2] < duration:
                    self.move_removed_cards(t - args[2])
                elif t - args[2] > duration:
                    self.cards_on_table_positions_p1 = []
                    self.cards_on_table_positions_p2 = []
                    self.cards_on_table = []
                    self.activated_turn_end = False
                    to_remove.append("TURN_ENDED")
                    self.data = self.network.send(Commands.END_TURN)

        for rem in to_remove:
            self.timed_actions[0].pop(rem)

    def render(self) -> None:
        self.win.fill(Colors.white.c)
        self.canvas.fill(self.background_color)
        self.info_canvas.fill(self.background_color)
        self.match_over_menu_canvas.fill(self.attributes["__var_match_over_menu_color"])

        # Draw here

        self.render_timed_actions()

        if self.game_state is ClientGameStates.GAME:
            self.render_game()
        elif self.game_state is ClientGameStates.LOBBY:
            self.render_lobby()
        elif self.game_state is ClientGameStates.MAIN_MENU:
            self.render_menu()
        elif self.game_state is ClientGameStates.MATCH_OVER_MENU:
            self.render_match_over_menu()

        self.render_info()

        self.win.blit(self.canvas, (0, 0))
        self.win.blit(self.info_canvas, (self.canvas.get_width(), 0))

        pygame.display.update()
        self.clock.tick(self.__fps)

    def render_menu(self) -> None:
        self.title.render()
        self.play_btn.render()
        self.options_btn.render()

    def render_lobby(self) -> None:
        for container in self.lobby_game_containers:
            container.render()

        self.create_new_game_button.render()
        self.nickname_input_field.render()

        if self.animation_handler.has("#CREATE_NEW_GAME"):
            self.lobby_new_game_container.render()

    def render_match_over_menu(self) -> None:
        # TODO: now

        self.match_over_menu_title.render()

        self.menu_return_button.render()
        self.menu_play_again_button.render()

        self.canvas.blit(self.match_over_menu_canvas, (0, 0))

    def render_info(self) -> None:
        pygame.draw.line(self.info_canvas, self.attributes["__var_info_canvas_line_color"],
                         (0, 0), (0, self.info_canvas.get_height()))  # (0, 9) (0, height - 8)

        if self.game_state is not ClientGameStates.GAME:
            return

        Label.render_text(self.info_canvas, "INFO", (10, 10), self.assets.font24,
                          self.attributes["__var_info_canvas_text_color"], bold=True, centered=False)
        pygame.draw.line(self.info_canvas, self.attributes["__var_info_canvas_line_color"],
                         (8, 30), (self.info_canvas.get_width() - 8, 30))
        Label.render_text(
            self.info_canvas,
            "NA POTEZU: " + str(self.game.get_nickname(self.game.player_turn)
                                if self.game.player_turn != -1 else ""),
            (10, 40), self.assets.font18, self.attributes["__var_info_canvas_dark_text_color"],
            bold=True, centered=False
        )
        Label.render_text(
            self.info_canvas, "ADUT: " + str(self.game.adut), (10, 60), self.assets.font18,
            self.attributes["__var_info_canvas_dark_text_color"], bold=True, centered=False
        )
        Label.render_text(
            self.info_canvas, "GAMESTATE: " + str(self.game.get_current_game_state()).split(".")[1], (10, 80),
            self.assets.font18, self.attributes["__var_info_canvas_dark_text_color"], bold=True, centered=False
        )

        Label.render_text(self.info_canvas, "BODOVI", (10, 140), self.assets.font24,
                          self.attributes["__var_info_canvas_text_color"], bold=True, centered=False)
        pygame.draw.line(self.info_canvas, self.attributes["__var_info_canvas_line_color"],
                         (8, 160), (self.info_canvas.get_width() - 8, 160))

        self.render_score()

    def render_score(self) -> None:
        y = self.attributes["__render_score_y_value"]
        pygame.draw.rect(self.info_canvas, (10, 30, 50), [35, y - 20, self.info_canvas.get_width() - 70, 30])

        Label.render_text(self.info_canvas, "MI", ((self.info_canvas.get_width() + 70) // 4, y),
                          self.assets.font24, self.attributes["__var_info_canvas_text_color"], bold=True)
        Label.render_text(self.info_canvas, "VI", ((3 * self.info_canvas.get_width() - 70) // 4, y),
                          self.assets.font24, self.attributes["__var_info_canvas_text_color"], bold=True)

        pygame.draw.line(self.info_canvas, self.attributes["__var_info_canvas_line_color"],
                         (35, y + 10), (self.info_canvas.get_width() - 35, y + 10))
        pygame.draw.line(self.info_canvas, self.attributes["__var_info_canvas_line_color"],
                         (self.info_canvas.get_width() // 2, y - 20), (self.info_canvas.get_width() // 2, y + 240))

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
            str_p1 = str(game[self.__player % 2])
            str_p2 = str(game[not self.__player % 2])

            if game[self.__player % 2] is None:
                str_p1 = "-"
            if game[not self.__player % 2] is None:
                str_p2 = "-"
            Label.render_text(score_canvas, str_p1,
                              ((score_canvas.get_width() + 5) // 4, self.score_y_offset + i * 25),
                              self.assets.font24, self.attributes["__var_info_canvas_score_color"], bold=True)
            Label.render_text(score_canvas, str_p2,
                              ((3 * score_canvas.get_width() - 5) // 4, self.score_y_offset + i * 25),
                              self.assets.font24, self.attributes["__var_info_canvas_score_color"], bold=True)

        self.info_canvas.blit(score_canvas, (self.info_canvas.get_width() // 2 - score_canvas.get_width() // 2, y + 18))

        pygame.draw.line(self.info_canvas, self.attributes["__var_info_canvas_line_color"],
                         (35, 445), (self.info_canvas.get_width() - 35, 445))
        surf2 = pygame.Surface(self.info_canvas.get_size(), pygame.SRCALPHA)
        a = 255
        for i in range(35):
            a -= 7
            pygame.draw.rect(surf2, (*self.background_color, a),
                             [36, 444 - i, self.info_canvas.get_width() - 71, 1])
        self.info_canvas.blit(surf2, (0, 0))

        final_score = self.game.get_final_game_score()
        Label.render_text(self.info_canvas, str(final_score[self.__player % 2]),
                          ((self.info_canvas.get_width() + 70) // 4, 465),
                          self.assets.font24, self.attributes["__var_info_canvas_final_score_color"], bold=True)
        Label.render_text(self.info_canvas, str(final_score[not self.__player % 2]),
                          ((3 * self.info_canvas.get_width() - 70) // 4, 465),
                          self.assets.font24, self.attributes["__var_info_canvas_final_score_color"], bold=True)

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
                if not self.shown_zvanja_points:
                    self.shown_zvanja_points = True
                    self.render_zvanja_points()
                self.render_game_zvanje()

        if self.animation_handler.has("#MATCH_OVER_SCREEN_FALL"):
            self.match_over_menu_title.render()
            self.menu_return_button.render()
            self.menu_play_again_button.render()
            self.canvas.blit(self.match_over_menu_canvas,
                             (0, self.animation_handler.get_animation("#MATCH_OVER_SCREEN_FALL").get_current_data()))

    def render_calling_adut(self) -> None:
        surf = pygame.Surface(self.canvas.get_size(), pygame.SRCALPHA)
        surf.fill((0, 0, 0))
        surf.set_alpha(self.attributes["__render_calling_adut_bg_alpha"])
        self.canvas.blit(surf, (0, 0))

        for button in self.call_adut_buttons:
            button.render()

        if self.game.count_dalje < 3:
            self.dalje_button.render()

    def render_zvanja_points(self) -> None:
        for player in range(len(self.game.final_zvanja)):
            if not self.game.final_zvanja[player]:
                continue
            i = player
            if self.__player > 1:
                player = player + 2
                if player > 3:
                    player -= 4

            zvanja = self.game.zvanja[i]
            zvanja_render_length = sum(len(z) * self.attributes["__render_zvanja_card_width"] for z in zvanja) + \
                (len(zvanja) - 1) * self.attributes["__render_zvanja_gap"]

            x, y = self.zvanja_card_positions[player]
            if player in (0, 3):
                x += zvanja_render_length // 2 + self.attributes["__render_zvanja_gap"] * 2
            else:
                x -= zvanja_render_length // 2 + self.attributes["__render_zvanja_gap"] * 2

            self.add_appearing_text(
                (x, y), f"+{sum(self.game.get_zvanje_value(z)[0] for z in self.game.zvanja[i])}",
                (0, 0, 100), self.attributes["__var_zvanja_points_appear_duration"], self.assets.font32
            )

    def render_zvanja(self) -> None:
        surf = pygame.Surface((self.canvas.get_width(), 140), pygame.SRCALPHA)
        surf.fill((0, 0, 0))
        surf.set_alpha(self.attributes["__render_zvanja_bg_alpha"])
        self.canvas.blit(surf, (0, self.canvas.get_height() // 2 - surf.get_height() // 2 - 30))

        self.zvanja_label.render()
        self.ima_zvanja_button.render()
        self.nema_zvanja_button.render()

    def render_game_zvanje(self) -> None:
        zvanja_gap = self.attributes["__render_zvanja_gap"]
        card_width = self.attributes["__render_zvanja_card_width"]
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
            if i >= len(cards): continue
            card = cards[i]
            x = self.inventory[i].x
            y = self.inventory[i].y
            alpha = self.inventory[i].angle
            card = pygame.transform.rotate(self.assets.card_images[card], -82 - alpha)
            self.render_card_outline(card, x, y, self.switched_cards_marker_color)

        for i in self.selected_cards_for_bela:
            if isinstance(i, (int, slice, )) and i < len(cards):
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
            if i == self.moving_card or self.selected_cards[i] or i >= len(self.inventory):
                continue
            if (
                    self.game.get_current_game_state() is GameState.ZVANJA and
                    self.game.get_zvanje_state() == 1 and
                    self.game.card_in_player_zvanja(card, self.__player)
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

            if (
                    i in self.selected_cards_for_bela and
                    isinstance(self.selected_cards_for_bela[0], int) and
                    isinstance(self.selected_cards_for_bela[1], int)
            ):
                if abs(self.selected_cards_for_bela[0] - self.selected_cards_for_bela[1]) > 1:
                    self.render_card_outline(card, x, y, self.called_bela_marker_color)
                elif i == min(self.selected_cards_for_bela):
                    self.render_card_outline(card, x, y, self.called_bela_marker_color)

            self.canvas.blit(card, (x - card.get_width() // 2, y - card.get_height() // 2))

        for i, card in enumerate(cards):
            if i == self.moving_card or not self.selected_cards[i] or i >= len(self.inventory):
                continue
            if (
                    self.game.get_current_game_state() is GameState.ZVANJA and
                    self.game.get_zvanje_state() == 1 and
                    self.game.card_in_player_zvanja(card, self.__player)
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
            for i, card in enumerate(self.cards_on_table):
                if card is None or not self.cards_on_table_positions_p2:
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
                    card.card == self.timed_actions[0]["DISPLAY_CARD_PLAYED"][3].card
            ):
                action = self.timed_actions[0]["DISPLAY_CARD_PLAYED"]
                current_time = time.time() - action[2]
                if action[0] and current_time < action[1]:
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

            cards = self.game.get_netalon(p)
            if self.game.dalje[p] or self.game.get_current_game_state() is not GameState.ZVANJE_ADUTA:
                cards = self.game.cards[p].sve

            alpha = (98 if rot else -82) - len(cards) * k // 2
            for card in cards:
                if (
                        self.game.get_current_game_state() is GameState.ZVANJA and
                        self.game.get_zvanje_state() == 1 and
                        self.game.card_in_player_zvanja(card, p)
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
        to_add = []

        for action, args in sorted(self.timed_actions[1].items(), key=lambda x: x[0] == "APPEAR_TEXT"):
            t = time.time()
            duration = 0
            if len(args) > 1:
                duration = args[1]

            if action == "DISPLAY_CARD_ERROR" and args[0] and t - args[2] < duration:
                self.display_card_error(t - args[2])

            if action == "GAME_OVER" and args[0]:
                self.display_game_over(t - args[2], fade_out=not self.game.is_match_over())
                if t - args[2] >= duration:
                    if not self.ended_game:
                        self.end_game = True
                        self.ended_game = True
                    if not self.game.is_match_over():
                        to_remove.append("GAME_OVER")

            if action == "BELOT" and args[0]:
                self.display_belot(t - args[2])
                if t - args[2] >= duration:
                    if "MATCH_OVER" not in self.timed_actions:
                        self.activated_match_over = True
                        to_add.append(["MATCH_OVER", True, self.timed_actions_durations["MATCH_OVER"],
                                       "BELOT", time.time()])
                    to_remove.append("BELOT")

            if action == "MATCH_OVER" and args[0]:
                self.ended_game = False
                if "GAME_OVER" in self.timed_actions[1]:
                    to_remove.append("GAME_OVER")
                else:
                    self.display_match_over(t - args[3], args[2])

                if t - args[3] >= duration:
                    self.animation_handler.add_animation(
                        AnimationFactory.create_falling_screen_animation(self.canvas.get_size()),
                        id_="#MATCH_OVER_SCREEN_FALL"
                    )

            if action == "APPEAR_TEXT":
                for data in args:
                    if data[0] and t - data[2] < data[1]:
                        if data[7] is None:
                            data[7] = self.assets.font24
                        self.appear_text(t - data[2], data[3], data[4], data[5], data[6], data[1], data[7])

        for k in to_remove:
            if k in self.timed_actions[1]:
                self.timed_actions[1].pop(k)

        for k in to_add:
            self.timed_actions[1][k[0]] = k[1:]

    def end_current_game(self) -> None:
        self.data = self.network.send(Commands.END_GAME)
        self.end_game = False
        self.started_new_game = False

    def end_current_match(self) -> None:
        self.data = self.network.send(Commands.END_MATCH)
        self.end_match = False

    def start_new_game(self) -> None:
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
        self.shown_zvanja_points = False
        self.calling_bela = False
        self.bela_just_called = False

        self.activated_turn_end = False
        self.activated_game_over = False
        self.activated_match_over = False
        self.ended_game = False
        self.end_game = False
        self.end_match = False
        self.started_new_game = True

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

    def call_bela(self) -> None:
        idx = 0
        for i, card in enumerate(self.inventory):
            if card.card in (("kralj", self.game.get_adut()), ("baba", self.game.get_adut())):
                self.selected_cards_for_bela[idx] = i
                idx = 1

        if None in self.selected_cards_for_bela:
            self.selected_cards_for_bela = [None, None]
        else:
            self.timed_actions[0]["CALL_BELA"] = [True, self.timed_actions_durations["CALL_BELA"], time.time()]
            self.calling_bela = True

    def sync_inventory(self) -> None:
        org_cards = self.get_cards().sve
        if self.game.get_current_game_state() is GameState.ZVANJE_ADUTA and not self.adut_dalje:
            org_cards = self.get_cards().netalon

        for i, inv_card in enumerate(self.inventory):
            if org_cards[i] != inv_card.card:
                self.inventory[i].card = org_cards[i]

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

        if self.game.called_belot:
            self.timed_actions[1]["BELOT"] = [True, self.timed_actions_durations["BELOT"], time.time()]

    def add_appearing_text(self, pos: Tuple[int, int], text: str, color: Tuple[int, int, int], duration: float,
                           font: pygame.font.SysFont = None) -> None:
        if "APPEAR_TEXT" not in self.timed_actions[1]:
            self.timed_actions[1]["APPEAR_TEXT"] = []
        self.timed_actions[1]["APPEAR_TEXT"].append([True, duration, time.time(), pos[0], pos[1], text, color, font])

    # Timed action functions

    def display_card_error(self, current_time: float) -> None:
        value = 0.2 - abs(current_time - 0.2)
        alpha = max(min(int(value * 500), 255), 0)

        rect = pygame.Rect(self.canvas.get_width() // 2 - 60, self.canvas.get_height() // 2 - 60, 120, 120)
        surf = pygame.Surface((120, 120), pygame.SRCALPHA)
        pygame.draw.rect(surf, (255, 0, 0, alpha), (0, 0, 120, 120), 0, 4)
        self.timed_actions_before_canvas.blit(surf, rect)

    def display_game_over(self, current_time: float, fade_out: bool = True) -> None:
        value = current_time
        if fade_out:
            value = 4 - abs(current_time - 4)
        alpha = max(min(int(value * 800), 255), 0)

        surf = pygame.Surface(self.canvas.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(surf, (0, 0, 0, 150), self.canvas.get_rect())

        self.game_over_label.set_surface(surf)
        self.game_over_label.render()

        str_team1 = self.game.get_nickname(0) + " & " + self.game.get_nickname(2)
        str_team2 = self.game.get_nickname(1) + " & " + self.game.get_nickname(3)
        k1 = len(str_team2) - len(str_team1)
        k2 = -k1
        str_team = " " * max(k1, 0) + str_team1 + "  -  " + str_team2 + " " * max(k2, 0)

        str_p1 = str(self.game.points[0])
        str_p2 = str(self.game.points[1])
        if self.game.points[0] is None:
            str_p1 = "\\"
        if self.game.points[1] is None:
            str_p2 = "\\"
        k1 = len(str_p2) - len(str_p1)
        k2 = -k1

        str_p = " " * max(k1, 0) + str_p1 + "  -  " + str_p2 + " " * max(k2, 0)

        self.game_over_label2.set_surface(surf)
        self.game_over_label2.render()
        self.game_over_label2.set_text(str_team + " \n " + str_p)

        surf.set_alpha(alpha)

        self.timed_actions_after_canvas.blit(surf, (0, 0))

    def display_belot(self, current_time: float) -> None:
        alpha = max(min(int(current_time * 800), 255), 0)

        surf = pygame.Surface(self.canvas.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(surf, (0, 0, 0, 150), self.canvas.get_rect())

        self.belot_label.set_surface(surf)
        self.belot_label.render()

        belot_player = -1
        for i, zvanja in enumerate(self.game.final_zvanja):
            for zvanje in zvanja:
                if zvanje[1] == "belot":
                    belot_player = i
                    break

        Label.render_text(
            surf,
            self.game.get_nickname(belot_player),
            (self.canvas.get_width() // 2, self.canvas.get_height() // 2 + 20),
            self.assets.font24,
            (200, 200, 200),
            bold=True
        )

        surf.set_alpha(alpha)

        self.timed_actions_after_canvas.blit(surf, (0, 0))

    def display_match_over(self, current_time: float, transition_type: str) -> None:
        surf = pygame.Surface(self.canvas.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(surf, (0, 0, 0, 150), self.canvas.get_rect())

        if transition_type == "BELOT":
            label_1 = self.belot_label
            label_2 = None
            id_ = "BELOT_TEXT"
        elif transition_type == "GAME":
            label_1 = self.game_over_label
            label_2 = self.game_over_label2
            id_ = "GAME_OVER_TEXT"
        else:
            return

        extra_labels = None
        label_1.set_surface(surf)
        label_1.render()
        if label_2:
            label_2.set_surface(surf)
            label_2.render()
            extra_labels = [label_2]

        self.match_over_label.set_surface(surf)
        self.match_over_label.render()

        if not self.animation_handler.has("#" + id_):
            self.animation_handler.add_animation(
                AnimationFactory.create_text_shoot_down_animation(
                    label_1, self.match_over_label,
                    self.win.get_height() + self.attributes["__var_belot_text_animation_stop_point"],
                    extra_labels=extra_labels
                ), id_="#" + id_
            )

        if self.animation_handler.get_animation("#" + id_).is_just_finished():
            str_team1 = self.game.get_nickname(0) + " & " + self.game.get_nickname(2)
            str_team2 = self.game.get_nickname(1) + " & " + self.game.get_nickname(3)
            k1 = len(str_team2) - len(str_team1)
            k2 = -k1
            self.add_appearing_text((self.canvas.get_width() // 2, self.canvas.get_height() // 2 + 50),
                                    " " * max(k1, 0) + str_team1 + "  -  " + str_team2 + " " * max(k2, 0),
                                    (200, 200, 200), 6, font=self.assets.font24)

            str_p1 = str(self.game.points[0])
            str_p2 = str(self.game.points[1])
            if self.game.points[0] is None:
                str_p1 = "\\"
            if self.game.points[1] is None:
                str_p2 = "\\"
            k1 = len(str_p2) - len(str_p1)
            k2 = -k1
            self.add_appearing_text((self.canvas.get_width() // 2, self.canvas.get_height() // 2 + 80),
                                    " " * max(k1, 0) + str_p1 + "  -  " + str_p2 + " " * max(k2, 0),
                                    (200, 200, 200), 6, font=self.assets.font24)

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
                        if j == len(positions) - 1 and i == 3:
                            self.timed_actions[0]["TURN_ENDED"][2] -= 100

    def appear_text(self, current_time: float, x: int, y: int, text: str, color: Tuple[int, int, int], duration: float,
                    font: pygame.font.SysFont) -> None:
        value = duration / 2 - abs(current_time - duration / 2)
        alpha = max(min(255, int(value * 600)), 0)

        Label.render_text(self.timed_actions_after_canvas, text, (x, y), font, color, bold=True, alpha=alpha)

    def move_back_card(self, current_time: float, card: int, copy_card: Card) -> None:
        card_x, card_y = copy_card.get_pos()
        org_x, org_y = copy_card.def_pos

        vel = [org_x - card_x, org_y - card_y]
        dist = math.sqrt((org_x - card_x) ** 2 + (org_y - card_y) ** 2)

        self.inventory[card].x += vel[0] * min(max(abs(dist), 50), 60) / 1000
        self.inventory[card].y += vel[1] * min(max(abs(dist), 50), 60) / 1000

        self.timed_actions[0]["MOVE_BACK_CARD"] = [True, self.timed_actions_durations["MOVE_BACK_CARD"],
                                                   time.time(), card, copy_card]

        if (
                math.sqrt((org_x - self.inventory[card].x) ** 2 + (org_y - self.inventory[card].y) ** 2) <= 10 or
                (self.inventory[card].y > org_y and vel[1] > 0) or
                (self.inventory[card].y < org_y and vel[1] < 0) or
                (self.inventory[card].x > org_x and vel[0] > 0) or
                (self.inventory[card].x < org_x and vel[0] < 0)
        ):
            self.inventory[card].move_back()
            self.timed_actions[0]["MOVE_BACK_CARD"] = [False, self.timed_actions_durations["MOVE_BACK_CARD"],
                                                       0, card, copy_card]

    def get_cards(self) -> Hand:
        return self.game.cards[self.__player]

    def get_player(self) -> int:
        return self.__player

    def on_turn(self):
        return self.__player == self.game.player_turn

    @property
    def game(self) -> Any:
        return self.data["game"]


if __name__ == "__main__":
    client = Client()
