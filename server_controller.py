import pickle
import socket
import time
from _thread import start_new_thread

from bela.game.networking.network import Network
from bela.game.utils.log import Log


class ServerControllerSS:

    def __init__(self, server) -> None:
        self.server = server

    def run(self) -> None:
        while True:

            conn, addr = self.server.server_controller_socket.accept()
            start_new_thread(self.run_, (conn, addr, ))
            break

        Log.nl()
        Log.i("SERVER", "Server Controller activated!")

    def run_(self, connection, address) -> None:
        while True:
            try:
                command = pickle.loads(connection.recv(self.server.buffer))

                response = "ok"

                cmnds = command.split()

                if cmnds and cmnds[0].lower() == "exec":
                    try:
                        exec(command[5:])
                    except Exception as e:
                        response = str(e)

                if cmnds and cmnds[0].lower() == "cc":
                    try:
                        game_idx = 0
                        player = 0
                        idx = 0
                        if "-g" in cmnds:
                            game_idx = int(cmnds[cmnds.index("-g")+1])
                        if "-p" in cmnds:
                            player = int(cmnds[cmnds.index("-p")+1])
                        if "-c" in cmnds:
                            idx = int(cmnds[cmnds.index("-c")+1])
                        if "-n" in cmnds:
                            c = cmnds[cmnds.index("-n")+1]
                            c = c.split("-")
                            c = (c[0], c[1]) if c[1] in ("karo", "herc", "tref", "pik") else (c[1], c[0])
                            idx = self.server.games[game_idx].cards[player].sve.index(c)

                        card = cmnds[-1]
                        card = card.split("-")
                        card = (card[0], card[1]) if card[1] in ("karo", "herc", "tref", "pik") else (card[1], card[0])

                        self.server.games[game_idx].cards[player].sve[idx] = card
                    except Exception as e:
                        response = str(e)

                if cmnds and cmnds[0].lower() == "auto":
                    try:
                        val = True
                        game_idx = 0
                        if "-g" in cmnds:
                            game_idx = int(cmnds[cmnds.index("-g")+1])
                        if "-s" in cmnds:
                            val = False
                        if "-all" in cmnds:
                            self.server.games[game_idx].auto_play = [val] * 4
                        for cmnd in cmnds[1:]:
                            if "-" in cmnd:
                                break
                            self.server.games[game_idx].auto_play[int(cmnd)] = val
                    except Exception as e:
                        response = str(e)

                if cmnds and cmnds[0].lower() == "belot":
                    try:
                        game_idx = 0
                        player = 0
                        color = "herc"
                        if "-g" in cmnds:
                            game_idx = int(cmnds[cmnds.index("-g")+1])
                        if "-p" in cmnds:
                            player = int(cmnds[cmnds.index("-p")+1])
                        if "-c" in cmnds:
                            color = cmnds[cmnds.index("-c")+1]

                        if color not in ("pik", "herc", "karo", "tref"):
                            raise ValueError("Invalid card color.")

                        cards = [(value, color) for value in ["7", "8", "9", "cener", "unter", "baba", "kralj", "kec"]]
                        for i, card in enumerate(cards):
                            self.server.games[game_idx].cards[player].sve[i] = card
                    except Exception as e:
                        response = str(e)

                if cmnds and cmnds[0].lower() == "p+":
                    try:
                        game_idx = 0
                        idx = int(cmnds[1])
                        points = int(cmnds[2])
                        if "-g" in cmnds:
                            game_idx = int(cmnds[cmnds.index("-g") + 1])

                        self.server.games[game_idx].games.append([points * (1 - idx), points * idx])
                    except Exception as e:
                        response = str(e)

                connection.sendall(pickle.dumps(response))
            except socket.error:
                Log.e("SERVER", "Server controller closed!")
                break


class ServerControllerCS:

    def __init__(self) -> None:
        self.network = Network(buffer=4096, port=22223)
        self.network.connect()

        while True:
            command = Log.input("", "Server Controller -v 1.0/~cmd $ ")

            if command.lower() == "w":
                lines = []
                line = Log.input_raw("0~ ")
                while line.lower() != "send":
                    lines.append(line)
                    line = Log.input_raw(f"{len(lines)}~ ")

                command = "exec " + "".join(line + "\n" for line in lines)

            try:
                response = self.network.send(command)
                if response == "ok":
                    Log.i("[SERVER]", response)
                else:
                    Log.e("[SERVER]", response)
            except socket.error:
                Log.e("[SERVER]", "Server closed.")
                time.sleep(3)
                return


if __name__ == "__main__":
    ServerControllerCS()
