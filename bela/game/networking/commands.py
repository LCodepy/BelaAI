from dataclasses import dataclass
from typing import Any


@dataclass
class Command:

    name: str
    data: Any


class Commands:

    GET = Command("GET", None)
    READY_UP = Command("READY_UP", None)

    @staticmethod
    def equals(c1: Command, c2: Command) -> bool:
        return c1.name == c2.name

    @staticmethod
    def str_equals(c1: Command, s1: str) -> bool:
        return c1.name == s1

