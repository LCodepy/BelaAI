import pickle
import random
import socket
import string
from _thread import start_new_thread

from bela.game.networking.commands import Commands
from server_controller import ServerControllerSS
from ..main.bela import Bela, GameState
from ..utils.log import Log


class Server:

    def __init__(self):
        Log.clear()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((socket.gethostname(), 22222))

        self.socket.listen()

        self.buffer = 4096

        self.games = {}
        self.clients = []
        self.admins = {}

        self.current_client = -1

        Log.i("SERVER", f"Started on port {22222}")

        self.server_controller = None
        self.server_controller_activated = Log.input("SERVER", f"Activate server control (Y/N): ").upper() == "Y"
        if self.server_controller_activated:
            self.server_controller_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_controller_socket.bind((socket.gethostname(), 22223))
            self.server_controller_socket.listen()
            self.server_controller = ServerControllerSS(self)

            start_new_thread(self.server_controller.run, ())
            Log.i("SERVER", "Activating server control...")

        while True:

            connection, address = self.socket.accept()
            Log.i("SERVER", "Client connected from " + str(address))

            self.clients.append(address)
            self.current_client += 1

            start_new_thread(self.client, (connection, address))

    def client(self, connection, address):
        client_id = "#" + "".join(random.choices(string.ascii_letters + string.digits, k=6))

        connection.send(pickle.dumps(client_id))

        nickname = f"Player {self.current_client+1}"
        connection.send(pickle.dumps(nickname))

        game_name = None
        last_game_name = None
        player_id = 0

        while True:
            try:
                entered_game = None
                joined_game = False
                while not joined_game:
                    try:
                        data = pickle.loads(connection.recv(self.buffer))

                        if last_game_name in self.games:
                            self.games[last_game_name].players_ready[player_id] = True
                            if all(self.games[last_game_name].players_ready):
                                self.games.pop(last_game_name)
                                self.admins.pop(last_game_name)
                                last_game_name = None

                        response = {"games": self.games, "admins": self.admins, "error": None, "nickname": nickname}

                        if Commands.equals(data, Commands.CREATE_GAME):
                            game_data = data.data[0]
                            if game_data.name in self.games:
                                response["error"] = f"Igra {game_data.name} već postoji"
                            else:
                                self.games[game_data.name] = Bela(game_data.max_points, game_data.team_names)
                                self.admins[game_data.name] = client_id

                        elif Commands.equals(data, Commands.REMOVE_GAME):
                            idx = data.data[0]
                            if idx >= len(self.games):
                                response["error"] = f"Igra ne postoji"
                            else:
                                game_name = ""
                                for i, (name, _) in enumerate(sorted(self.games.items(), key=lambda g: g[1].start_time)):
                                    if idx == i:
                                        game_name = name

                                self.games.pop(game_name)
                                self.admins.pop(game_name)

                        elif Commands.equals(data, Commands.ENTER_GAME):
                            game_name = data.data[0]
                            g = self.games[game_name]
                            entered_game = g
                            if not g.add_player(nickname, 0):
                                if not g.add_player(nickname, 1):
                                    response["error"] = f"Igra {game_name} je već popunjena"
                                    entered_game = None

                        elif Commands.equals(data, Commands.CHANGE_NICKNAME):
                            nickname = data.data[0]

                        elif Commands.equals(data, Commands.DISCONNECT):
                            Log.i("SERVER", f"Client {address} disconnected...")
                            connection.sendall(pickle.dumps("OK"))
                            connection.close()
                            self.clients.pop(self.clients.index(address))
                            return

                        if entered_game and entered_game.is_full() and Commands.equals(data, Commands.GET):
                            joined_game = True
                            response["start_game"] = True
                            response["game"] = self.games[game_name]
                            response["data"] = {}
                            player_id = self.games[game_name].player_data.index(nickname)
                            print("SERVER", nickname, ": ", player_id)

                        connection.sendall(pickle.dumps(response))

                    except (socket.error, EOFError, ):
                        Log.e("SERVER", f"Client {address} disconnected...")
                        self.clients.pop(self.clients.index(address))
                        break

                while True:

                    try:
                        if game_name not in self.games:
                            break

                        data = pickle.loads(connection.recv(self.buffer))

                        game = self.games[game_name]
                        game.set_nickname(player_id, nickname)

                        response = {"game": None, "games": self.games, "admins": self.admins, "error": None, "nickname": nickname, "data": {}}

                        # Check commands

                        if Commands.equals(data, Commands.PLAY_CARD):
                            if game.get_current_game_state() != GameState.IGRA or game.player_turn != player_id:
                                passed = False
                            else:
                                passed = game.inspect_played_card(data.data[0].card, player_id)

                            response["data"]["passed"] = passed
                            if passed:
                                game.add_card_to_table(data.data[0], player_id)
                                game.cards[player_id].remove(data.data[0].card)

                        if Commands.equals(data, Commands.SWAP_CARDS):
                            game.swap_cards_for_player(player_id, data.data[0])

                        if Commands.equals(data, Commands.SORT_CARDS):
                            game.sort_player_cards(player_id)

                        if Commands.equals(data, Commands.CALL_ADUT):
                            game.set_adut(data.data[0])
                            game.adut_caller = player_id
                            game.next_game_state()

                        if Commands.equals(data, Commands.DALJE):
                            game.count_dalje += 1
                            game.dalje[player_id] = True
                            game.next_turn()

                        if Commands.equals(data, Commands.ZVANJE):
                            game.add_zvanja(data.data[0], player_id)
                            game.zvanje_over[player_id][0] = True
                            if all(map(lambda x: x[0], game.zvanje_over)):
                                game.calculate_zvanja()

                        if Commands.equals(data, Commands.ZVANJE_GOTOVO):
                            game.zvanje_over[player_id][0] = True
                            game.zvanje_over[player_id][1] = True
                            if all(map(lambda x: x[1], game.zvanje_over)) and game.get_current_game_state() is GameState.ZVANJA:
                                game.next_game_state()

                        if Commands.equals(data, Commands.CALLED_BELA):
                            game.called_bela = True
                            game.player_called_bela = player_id

                        if Commands.equals(data, Commands.END_TURN):
                            game.end_turn(player_id)

                        if Commands.equals(data, Commands.END_GAME):
                            game.end_game(player_id)

                        if Commands.equals(data, Commands.CLOSE_GAME):
                            game.player_leave(player_id)

                        self.games[game_name] = game

                        response["game"] = game

                        connection.sendall(pickle.dumps(response))

                        if not any(game.players):
                            last_game_name = game_name
                            break

                    except (socket.error, EOFError, ):
                        Log.i("SERVER", f"Player {player_id} from game {game_name} disconnected.")
                        if game_name in self.games:
                            self.games.pop(game_name)
                        break

            except (socket.error, EOFError,):
                Log.e("SERVER", f"Client {address} disconnected...")
                self.clients.pop(self.clients.index(address))
                break

        connection.close()


if __name__ == "__main__":
    server = Server()
