from colorama import Fore


disabled = False


class Log:

    @staticmethod
    def i(tag: str, text: str) -> None:
        if not disabled:
            print(Fore.BLUE + "I/" * int(len(tag) != 0) + tag + ":" * int(len(tag) != 0), text)

    @staticmethod
    def e(tag: str, text: str) -> None:
        if not disabled:
            print(Fore.RED + "E/" * int(len(tag) != 0) + tag + ":" * int(len(tag) != 0), text)

    @staticmethod
    def disable(b: bool) -> None:
        global disabled
        disabled = b

