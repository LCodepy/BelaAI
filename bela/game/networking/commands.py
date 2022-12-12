from dataclasses import dataclass
from typing import Any

from bela.game.main.bela import Card, GameData


@dataclass
class Command:

    name: str
    data: Any


class Commands:

    GET = Command("GET", None)
    CREATE_GAME = Command("CREATE_GAME", (GameData, ))
    REMOVE_GAME = Command("REMOVE_GAME", (int, ))
    ENTER_GAME = Command("ENTER_GAME", (str, ))
    CHANGE_NICKNAME = Command("CHANGE_NICKNAME", (str, ))
    READY_UP = Command("READY_UP", None)
    SORT_CARDS = Command("SORT_CARDS", None)
    PLAY_CARD = Command("PLAY_CARD", (Card, ))
    SWAP_CARDS = Command("SWAP_CARDS", (int, int))
    CALL_ADUT = Command("CALL_ADUT", (str, ))
    DALJE = Command("DALJE", None)
    ZVANJE = Command("ZVANJE", (list, ))
    ZVANJE_GOTOVO = Command("ZVANJE_GOTOVO", None)
    CALLED_BELA = Command("CALLED_BELA", None)
    END_TURN = Command("END_TURN", None)
    END_GAME = Command("END_GAME", None)
    END_MATCH = Command("END_MATCH", None)

    @staticmethod
    def new(c: Command, *args) -> Command:
        return Command(c.name, args)

    @staticmethod
    def equals(c1: Command, c2: Command) -> bool:
        return c1.name == c2.name

    @staticmethod
    def str_equals(c1: Command, s1: str) -> bool:
        return c1.name == s1

