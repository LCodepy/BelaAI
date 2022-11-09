from enum import Enum, auto


class ClientGameStates(Enum):

    LOBBY = auto()
    GAME = auto()
    MAIN_MENU = auto()
    MATCH_OVER_MENU = auto()
    UNDEFINED = auto()

