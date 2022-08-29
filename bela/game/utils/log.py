import os

from colorama import Fore


disabled = False


class Log:

    @staticmethod
    def clear() -> None:
        os.system("cls")

    @staticmethod
    def i(tag: str, text: str) -> None:
        if not disabled:
            print(Fore.BLUE + "I/" * int(len(tag) != 0) + tag + ": " * int(len(tag) != 0) + text)

    @staticmethod
    def e(tag: str, text: str) -> None:
        if not disabled:
            print(Fore.RED + "E/" * int(len(tag) != 0) + tag + ": " * int(len(tag) != 0) + text)

    @staticmethod
    def input(tag: str, text: str) -> str:
        if not disabled:
            print(Fore.GREEN + "INPUT/" * int(len(tag) != 0) + tag + ": " * int(len(tag) != 0) + text,
                  end=" " * int(len(tag) + len(text) != 0))
            return input()
        return ""

    @staticmethod
    def input_raw(text: str) -> str:
        if not disabled:
            print(Fore.MAGENTA + text, end="")
            return input()
        return ""

    @staticmethod
    def nl() -> None:
        print()

    @staticmethod
    def disable(b: bool) -> None:
        global disabled
        disabled = b

