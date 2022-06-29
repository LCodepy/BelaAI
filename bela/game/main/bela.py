import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Tuple, Optional

import pygame


class GameState(Enum):

    ZVANJE_ADUTA = auto()
    ZVANJA = auto()
    IGRA = auto()
    BROJANJE = auto()


@dataclass
class Hand:

    netalon: list = field(default_factory=list)
    talon: list = field(default_factory=list)
    sve: list = field(default_factory=list)

    def remove(self, card: Tuple[str, str]) -> None:
        if card in self.netalon:
            self.netalon.pop(self.netalon.index(card))
        if card in self.talon:
            self.talon.pop(self.talon.index(card))
        if card in self.sve:
            self.sve.pop(self.sve.index(card))


class Card:

    def __init__(self, card, x, y, angle, rect, moving: bool = False) -> None:
        self.card = card
        self.x = x
        self.y = y
        self.angle = angle
        self.rect = rect
        self.moving = moving
        self.def_pos = (x, y)

    def set_pos(self, pos) -> None:
        self.x, self.y = pos

    def move_back(self) -> None:
        self.x, self.y = self.def_pos

    def collision_rect(self) -> pygame.Rect:
        x, y = self.def_pos
        return pygame.Rect(x - 7, y - 7, 14, 14)

    def get_pos(self) -> Tuple[int, int]:
        return self.x, self.y


class Bela:

    """
    Class that contains most of the game logic and features.
    """

    def __init__(self, id_: int) -> None:
        self.id = id_

        self.player_data = [
            {"nickname": "", "ready": False},
            {"nickname": "", "ready": True},
            {"nickname": "", "ready": True},
            {"nickname": "", "ready": True}
        ]  # TODO: Replace with False

        self.player_turn = 0

        # Game logic

        self.deck = []
        self.create_cards()
        self.rifle_shufle()

        self.cards = [Hand(), Hand(), Hand(), Hand()]
        self.deal_cards()

        self.current_state = GameState.ZVANJE_ADUTA

        self.cards_on_table = [None, None, None, None]

        self.adut = None
        self.count_dalje = 0
        self.dalje = [False, False, False, False]

    def create_cards(self) -> None:
        types = ["herc", "pik", "karo", "tref"]
        values = ["7", "8", "9", "cener", "unter", "baba", "kralj", "kec"]

        self.deck = [(v, t) for t in types for v in values]

    def rifle_shufle(self) -> None:
        random.shuffle(self.deck)

    def deal_cards(self) -> None:
        for i in range(32):
            if i < 24:
                self.cards[i % 4].netalon.append(self.deck.pop())
            else:
                self.cards[i % 4].talon.append(self.deck.pop())

        for i in range(4):
            self.cards[i].sve = self.cards[i].talon + self.cards[i].netalon

    def inspect_played_card(self, card: Tuple[str, str]) -> bool:
        return True  # TODO: Make the function check the rules

    def swap_cards_for_player(self, id_: int, cards: Tuple) -> None:
        c1, c2 = cards
        self.cards[id_].sve[c1], self.cards[id_].sve[c2] = self.cards[id_].sve[c2], self.cards[id_].sve[c1]

    def sort_player_cards(self, id_: int) -> None:
        list_sorted = []
        types = ["herc", "pik", "karo", "tref"]
        values = ["7", "8", "9", "cener", "unter", "baba", "kralj", "kec"]
        current = self.cards[id_].sve[:]

        if self.get_adut():
            types.remove(self.get_adut())

        for x in types:
            for y in values:
                if (y, x) in current:
                    list_sorted.append((y, x))
                    current.remove((y, x))

        if self.get_adut():
            values_adut = ["7", "8", "cener", "baba", "kralj", "kec", "9", "unter"]
            for x in values_adut:
                if (x, self.get_adut()) in current:
                    list_sorted.append((x, self.get_adut()))

        self.cards[id_].sve = list_sorted

    def next_turn(self) -> None:
        self.player_turn += 1
        if self.player_turn > 3:
            self.player_turn = 0

    def next_game_state(self) -> None:
        if self.current_state is GameState.ZVANJE_ADUTA:
            self.current_state = GameState.ZVANJA
        elif self.current_state is GameState.ZVANJA:
            self.current_state = GameState.IGRA
        elif self.current_state is GameState.IGRA:
            self.current_state = GameState.BROJANJE

    def set_adut(self, adut: str) -> None:
        self.adut = adut
        self.player_turn = 0

    def get_adut(self) -> Optional[str]:
        return self.adut

    def get_current_game_state(self) -> GameState:
        return self.current_state

    def get_card_index(self, id_: int, card: Tuple[str, str]) -> int:
        return self.cards[id_].sve.index(card)

    def set_nickname(self, id_: int, nickname: str) -> None:
        self.player_data[id_]["nickname"] = nickname

    def get_nickname(self, id_: int) -> str:
        return self.player_data[id_]["nickname"]

    def get_netalon(self, id_: int) -> list:
        return [card for card in self.cards[id_].sve if card in self.cards[id_].netalon]

    def ready_up_player(self, id_: int, value: bool) -> None:
        self.player_data[id_]["ready"] = value

    def is_player_ready(self, id_: int) -> bool:
        return self.player_data[id_]["ready"]

    def is_ready(self) -> bool:
        return all(list(map(lambda d: d["ready"], self.player_data)))

    def is_waiting(self) -> bool:
        return any(list(map(lambda d: d["ready"], self.player_data)))

    def get_ready_player_count(self) -> int:
        return sum(list(map(lambda d: d["ready"], self.player_data)))
