import traceback

from bela.game.networking.client import Client


if __name__ == "__main__":
    try:
        client = Client()
    except Exception:
        print(traceback.format_exc())
        input()
