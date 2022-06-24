import random
from dataclasses import dataclass, field


@dataclass()
class Hand:

    netalon: list = field(default_factory=list)
    talon: list = field(default_factory=list)
    sve: list = field(default_factory=list)


class Bela:

    """
    Class that contains most of the game logic and features.
    """

    def __init__(self, id_: int) -> None:
        self.id = id_

        self.player_data = [
            {"nickname": "", "ready": False},
            {"nickname": "", "ready": False},
            {"nickname": "", "ready": False},
            {"nickname": "", "ready": False}
        ]

        self.player_turn = 0

        # Game logic

        self.deck = []
        self.create_cards()
        self.rifle_shufle()

        self.cards = [Hand(), Hand(), Hand(), Hand()]
        self.deal_cards()

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

    def set_nickname(self, id_: int, nickname: str) -> None:
        self.player_data[id_]["nickname"] = nickname

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
