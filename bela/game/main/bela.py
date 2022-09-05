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

    def __init__(self, id_: int, max_points: int = 1001) -> None:
        self.id = id_
        self.max_points = max_points

        self.player_data = [
            {"nickname": "", "ready": False},
            {"nickname": "", "ready": True},
            {"nickname": "", "ready": True},
            {"nickname": "", "ready": True}
        ]  # TODO: Replace with False

        self.player_turn = 1
        self.diler = 0

        # Game logic

        self.deck = []
        self.create_cards()
        self.rifle_shufle()

        self.cards = [Hand(), Hand(), Hand(), Hand()]
        self.deal_cards()

        self.current_state = GameState.ZVANJE_ADUTA

        self.cards_on_table = []
        self.player_cards_on_table: list[Optional[str, str]] = [None, None, None, None]

        self.adut = None
        self.count_dalje = 0
        self.dalje = [False, False, False, False]

        self.zvanja = [[], [], [], []]
        self.zvanje_over = [[False, False] for _ in range(4)]
        self.final_zvanja = [[], [], [], []]

        self.points = [0, 0]
        self.stihovi = [[], [], [], []]

        self.turn_just_ended = False
        self.current_turn_winner = -1
        self.ready_to_end_turn = [False] * 4
        self.ready_to_end_game = [False] * 4

        self.current_game_over = False
        self.ended_last_turn = False

        self.games = []

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

    def strongest_card(self, cards: list[Tuple[str, str]]) -> Tuple[str, str]:
        data = [[card, self.get_card_value(card), card[1] == self.adut, cards[0][1] == card[1]] for card in cards]
        return sorted(data, key=lambda c: c[1] + c[2] * 1000 + c[3] * 100, reverse=True)[0][0]

    def inspect_played_card(self, card: Tuple[str, str], id_: int) -> bool:
        if not any(self.cards_on_table):
            return True

        first_card = self.cards_on_table[0].card
        strongest_card = self.strongest_card(list(map(lambda c: c.card, self.cards_on_table)))

        if card[1] != first_card[1]:
            if self.player_has_color(first_card[1], id_):  # played wrong color while having the right color
                return False
            if card[1] != self.adut and self.player_has_adut(id_):  # played wrong color while having adut
                return False
            if card[1] == self.adut and strongest_card[1] == self.adut and \
                    self.is_card_greater(strongest_card, card):  # played either < or > then strongest_card
                return not self.player_has_higher(strongest_card, id_)
        elif self.is_card_greater(card, strongest_card):  # played the card stronger then the strongest_card
            return True
        else:
            return not self.player_has_higher(strongest_card, id_)  # player either has or doesn't have bigger card
        return True

    def remove_cards_from_table(self) -> [int, int]:
        cards_on_table = list(map(lambda x: x.card, self.cards_on_table))
        stih_value = sum(list(map(self.get_real_card_value, cards_on_table)))
        first_card = cards_on_table[1]
        card_values = [[0, 0, 0][:] for _ in range(4)]

        for i, card in enumerate(cards_on_table):
            card_values[i][2] = int(card[1] == self.adut) * 1000
            card_values[i][1] = int(card[1] == first_card) * 100
            card_values[i][0] = self.get_card_value(card)

        values_filtered = [sum(d) for d in card_values]

        idx = values_filtered.index(max(values_filtered))
        player_turn = self.player_turn - 3
        if player_turn < 0:
            player_turn += 4
        ret = idx + player_turn
        if ret > 3:
            ret -= 4

        return ret, stih_value

    def player_has_adut(self, id_: int) -> bool:
        return any(card[1] == self.adut for card in self.cards[id_].sve)

    def player_has_higher(self, card: Tuple[str, str], id_: int) -> bool:
        return any(self.is_card_greater(c, card) for c in filter(lambda x: x[1] == card[1], self.cards[id_].sve))

    def player_has_color(self, color: str, id_: int) -> bool:
        return any(card[1] == color for card in self.cards[id_].sve)

    def is_card_greater(self, c1: Tuple[str, str], c2: Tuple[str, str]) -> bool:
        if c1[1] != c2[1]:
            return True
        return self.get_card_value(c1) > self.get_card_value(c2)

    def get_card_value(self, card: Tuple[str, str]) -> int:
        if card[0] == "9":
            if card[1] == self.adut:
                return 18
            return 9
        elif card[0] == "unter":
            if card[1] == self.adut:
                return 19
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

    def calculate_zvanja(self) -> None:
        # TODO: u ovoj funkciji sigurno nes ne valja jer moj mozak premali za ovakvu kompliciranost pa popravi to
        zvanja_values = [
            [self.get_zvanje_value(zvanje) for zvanje in self.zvanja[i]]
            for i in range(4)
        ]

        mx_zvanje = (0, "s")
        mx_idx = []
        for i in range(4):
            for zvanje in zvanja_values[i]:
                if zvanje[0] > mx_zvanje[0] or (zvanje[0] == mx_zvanje[0] and mx_zvanje[1] == "s" and zvanje[1] == "v"):
                    mx_idx.clear()
                    mx_idx.append(i)
                    mx_zvanje = zvanje
                elif zvanje[0] == mx_zvanje[0] and zvanje[1] == mx_zvanje[1]:
                    mx_idx.append(i)

        mn = 4
        mn_idx = 0
        for idx in mx_idx:
            rel_idx = idx - self.diler
            if rel_idx <= 0:
                rel_idx = 4 - rel_idx
            if rel_idx < mn:
                mn = rel_idx
                mn_idx = idx

        zvanja_winner = (1, 3) if mn_idx % 2 else (0, 2)

        self.final_zvanja[zvanja_winner[0]] = zvanja_values[zvanja_winner[0]]
        self.final_zvanja[zvanja_winner[1]] = zvanja_values[zvanja_winner[1]]

        self.points[mn_idx % 2] = sum(map(lambda x: x[0], zvanja_values[zvanja_winner[0]])) + sum(map(lambda x: x[0], zvanja_values[zvanja_winner[1]]))

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
        types = ["karo", "herc", "tref", "pik"]
        random.shuffle(types)

        card_count = {}
        card_types = {}
        for card in cards:
            if card[0] not in card_count:
                card_count[card[0]] = 0
            if card[1] not in card_types:
                card_types[card[1]] = []
            card_count[card[0]] += 1
            card_types[card[1]].append((card[0], self.get_zvanje_card_value(card)))

        zvanja4 = [
            [(card, type_) for type_ in types]
            for card, v in card_count.items()
            if v == 4 and card not in ("7", "8")
        ]

        all_zvanja_skala = []

        for type_, values in card_types.items():
            values.sort(key=lambda x: self.get_zvanje_card_value(x))
            skala = [0] * 8

            for value in values:
                skala[value[1]] = value[0]

            zvanje_skala = [[], []]
            idx = 0
            for i in range(8):
                if skala[i] and (not zvanje_skala[idx] or skala[i - 1]):
                    zvanje_skala[idx].append((skala[i], type_))
                elif len(zvanje_skala[idx]) < 3:
                    zvanje_skala[idx].clear()
                else:
                    idx = 1
            if len(zvanje_skala[0]) < 3:
                zvanje_skala.pop(0)
            if len(zvanje_skala[-1]) < 3:
                zvanje_skala.pop()

            all_zvanja_skala += zvanje_skala

        self.zvanja[id_] = zvanja4 + all_zvanja_skala

    def next_turn(self) -> None:
        self.player_turn += 1
        if self.player_turn > 3:
            self.player_turn = 0

    def set_turn(self, id_: int) -> None:
        self.player_turn = id_

    def end_turn(self, id_: int) -> None:
        self.ready_to_end_turn[id_] = True

        if all(self.ready_to_end_turn):
            self.stihovi[self.current_turn_winner].append([card.card for card in self.cards_on_table])
            self.set_turn(self.current_turn_winner)
            self.cards_on_table.clear()
            self.player_cards_on_table = [None] * 4
            self.turn_just_ended = False
            self.ready_to_end_turn = [False] * 4

            if not self.cards[0].sve and not self.ended_last_turn:
                self.current_game_over = True
                self.points[self.current_turn_winner % 2] += 10
                self.set_turn(-1)
                self.ended_last_turn = True

    def end_game(self, id_: int) -> None:
        self.ready_to_end_game[id_] = True

        if all(self.ready_to_end_game):
            self.current_game_over = False
            self.games.append(self.points)

            self.start_new_game()

    def start_new_game(self) -> None:
        self.diler += 1
        if self.diler > 3:
            self.diler = 0

        self.player_turn = self.diler + 1
        if self.player_turn > 3:
            self.player_turn = 0

        self.deck.clear()
        self.create_cards()
        self.rifle_shufle()
        self.cards = [Hand(), Hand(), Hand(), Hand()]
        self.deal_cards()

        self.current_state = GameState.ZVANJE_ADUTA

        self.cards_on_table.clear()
        self.player_cards_on_table = [None] * 4

        self.adut = None
        self.count_dalje = 0
        self.dalje = [False] * 4

        self.zvanja = [[], [], [], []]
        self.zvanje_over = [[False, False] for _ in range(4)]
        self.final_zvanja = [[], [], [], []]

        self.points = [0, 0]
        self.stihovi = [[], [], [], []]

        self.turn_just_ended = False
        self.current_turn_winner = -1
        self.ready_to_end_turn = [False] * 4
        self.ready_to_end_game = [False] * 4

        self.current_game_over = False
        self.ended_last_turn = False

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
            self.turn_just_ended = True
            self.set_turn(-1)
            self.current_turn_winner = turn
            self.points[turn % 2] += stih
        else:
            self.next_turn()

    def player_has_bela(self, id_: int) -> bool:
        return ("kralj", self.adut) in self.cards[id_].sve and ("baba", self.adut) in self.cards[id_].sve

    def get_zvanje_value(self, zvanje: list[Tuple[str, str]]) -> Tuple[int, str]:
        if len(zvanje) == 4 and zvanje[0][0] == zvanje[1][0]:
            v = zvanje[0][0]
            if v == "unter":
                return 200, "v"
            elif v == "9":
                return 150, "v"
            elif v not in ("7", "8"):
                return 100, "v"
        length = len(zvanje)
        if length == 3:
            return 20, "s"
        if length == 4:
            return 50, "s"
        if length == 8:
            return self.max_points, "belot"
        if length >= 5:
            return 100, "s"

    def get_zvanje_card_value(self, card: Tuple[str, str]) -> int:
        return ["7", "8", "9", "cener", "unter", "baba", "kralj", "kec"].index(card[0])

    def get_player_zvanja(self, id_: int) -> list[list[Tuple[str, str]]]:
        return self.zvanja[id_]

    def get_final_game_score(self) -> Tuple[int, int]:
        return sum(map(lambda x: x[0], self.games)), sum(map(lambda x: x[1], self.games))

    def set_adut(self, adut: str) -> None:
        self.adut = adut
        self.player_turn = self.diler + 1
        if self.player_turn > 3:
            self.player_turn = 0

    def get_adut(self) -> Optional[str]:
        return self.adut

    def get_zvanje_state(self) -> int:
        if all(map(lambda x: x[1], self.zvanje_over)):
            return 2
        if all(map(lambda x: x[0], self.zvanje_over)):
            return 1
        return 0

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
