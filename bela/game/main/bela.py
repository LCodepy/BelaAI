import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Tuple, Optional

import pygame
#lol

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

        self.cards_on_table = []
        self.player_cards_on_table = [None, None, None, None]

        self.adut = None
        self.count_dalje = 0
        self.dalje = [False, False, False, False]

        self.zvanja = [[], [], [], []]
        self.zvanje_over = [False, False, False, False]

        self.points = [0, 0]

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

    def inspect_played_card(self, card: Tuple[str, str], id_: int) -> bool:
        if not any(self.cards_on_table):
            return True

        last_card = self.cards_on_table[-1].card
        first_card = self.cards_on_table[0].card

        if card[1] != first_card[1]:
            if self.player_has_color(first_card[1], id_):
                return False
            if card[1] != self.adut and self.player_has_adut(id_):
                return False
            if card[1] == self.adut and last_card == self.adut:
                return not self.player_has_higher(last_card, id_)
            return True
        else:
            if self.is_card_greater(last_card, card) and last_card[1] == card[1]:
                return not self.player_has_higher(last_card, id_)
        return True

    def remove_cards_from_table(self) -> [int, int]:
        cards_on_table = list(map(lambda x: x.card, self.cards_on_table))
        stih_value = sum(list(map(self.get_real_card_value, cards_on_table)))
        first_card = cards_on_table[0]
        cards = [0, 0, 0, 0]

        for i, card in enumerate(cards_on_table):
            if card[1] not in [self.adut, first_card]:
                continue
            for j, c in enumerate(cards_on_table):
                if i == j:
                    continue
                if c[1] not in [self.adut, first_card]:
                    cards[i] += 1
                elif card[1] == c[1]:
                    if self.is_card_greater(card, c):
                        cards[i] += 1
                elif card[1] in [self.adut, first_card[1]]:
                    cards[i] += 1

        ret = self.player_cards_on_table.index(self.cards_on_table[cards.index(max(cards))]), stih_value
        self.cards_on_table.clear()
        self.player_cards_on_table = [None for _ in range(4)]
        return ret

    def player_has_adut(self, id_: int) -> bool:
        return any(card[1] == self.adut for card in self.cards[id_].sve)

    def player_has_higher(self, card: Tuple[str, str], id_: int) -> bool:
        return any(self.is_card_greater(c, card) for c in filter(lambda x: x[1] == card[1], self.cards[id_].sve))

    def player_has_color(self, color: str, id_: int) -> bool:
        return any(card[1] == color for card in self.cards[id_].sve)

    def is_card_greater(self, c1: Tuple[str, str], c2: Tuple[str, str]) -> bool:
        return self.get_card_value(c1) > self.get_card_value(c2)

    def get_card_value(self, card: Tuple[str, str]) -> int:
        if card[0] == "9":
            if card[1] == self.adut:
                return 19
            return 9
        elif card[0] == "unter":
            if card[1] == self.adut:
                return 18
            return 12
        if card[0] in "78":
            return int(card[0])
        elif card[0] == "baba":
            return 13
        elif card[0] == "kralj":
            return 14
        elif card[0] == "cener":
            return 15
        elif card[0] == "kec":
            return 16

    def get_real_card_value(self, card: Tuple[str, str]) -> int:
        if card[0] == "9":
            if card[1] == self.adut:
                return 14
            return 0
        elif card[0] == "unter":
            if card[1] == self.adut:
                return 20
            return 2
        if card[0] in "78":
            return 0
        elif card[0] == "baba":
            return 3
        elif card[0] == "kralj":
            return 4
        elif card[0] == "cener":
            return 10
        elif card[0] == "kec":
            return 11

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

    def add_zvanja(self, cards: list, id_: int) -> None:
        values = ["7", "8", "9", "cener", "unter", "baba", "kralj", "kec"]
        l = [[]]
        z = 0
        index = 0
        types = []
        number_of_types = []

        for card in cards:
            if card[0] not in types:
                types.append(card[0])
                number_of_types.append(0)
            else:
                number_of_types[types.index(card[0])] = number_of_types[types.index(card[0])] + 1
                if number_of_types[types.index(card[0])] == 3:
                    l[index].append((card[0], "tref"))
                    l[index].append((card[0], "karo"))
                    l[index].append((card[0], "herc"))
                    l[index].append((card[0], "pik"))
                    index += 1
                    l.append([])

        for y in range(len(cards[:-1])):
            if values.index(cards[y][0]) + 1 == values.index(cards[y + 1][0]) and cards[y][1] == cards[y + 1][1]:
                if z == 0:
                    l[index].append((cards[y][0], cards[y][1]))
                l[index].append(cards[y + 1])
                z += 1
            else:
                z = 0
                index += 1
                l.append([])

        zvanje = [i for i in l if len(i) > 2]
        self.zvanja[id_] = zvanje

    def next_turn(self) -> None:
        self.player_turn += 1
        if self.player_turn > 3:
            self.player_turn = 0

    def set_turn(self, id_: int) -> None:
        self.player_turn = id_

    def next_game_state(self) -> None:
        if self.current_state is GameState.ZVANJE_ADUTA:
            self.current_state = GameState.ZVANJA
        elif self.current_state is GameState.ZVANJA:
            self.current_state = GameState.IGRA
        elif self.current_state is GameState.IGRA:
            self.current_state = GameState.BROJANJE

    def add_card_to_table(self, card: Tuple[str, str], id_: int) -> None:
        self.cards_on_table.append(card)
        self.player_cards_on_table[id_] = card

        if len(self.cards_on_table) == 4:
            turn, stih = self.remove_cards_from_table()
            self.set_turn(turn)
            self.points[turn % 2] += stih
        else:
            self.next_turn()

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
