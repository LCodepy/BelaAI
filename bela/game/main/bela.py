

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

    def prepare_deck(self) -> None:
        pass

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
