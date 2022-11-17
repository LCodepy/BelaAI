import pickle
import socket
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

            start_new_thread(self.client, (connection, address))

    def client(self, connection, address):
        connection.send(pickle.dumps(address))

        while True:
            try:
                data = pickle.loads(connection.recv(self.buffer))

                response = {"games": self.games}

                if Commands.equals(data, Commands.CREATE_GAME):
                    pass

                elif Commands.equals(data, Commands.ENTER_GAME):
                    pass

                elif Commands.equals(data, Commands.CHANGE_NICKNAME):
                    pass

                connection.sendall(pickle.dumps(response))

            except (socket.error, EOFError, ):
                Log.i("SERVER", f"Client {address} disconnected...")
                connection.close()
                self.clients.pop(self.clients.index(address))
                break

        return  # TODO: remove

        while True:

            try:
                data = pickle.loads(connection.recv(self.buffer))

                if game_id not in self.games:
                    break

                game = self.games[game_id]
                game.set_nickname(player_id, nickname)

                response = {"game": None, "data": {}}

                # Check commands

                if Commands.equals(data, Commands.READY_UP):
                    game.ready_up_player(player_id, True)

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

                self.games[game_id] = game

                response["game"] = game

                connection.sendall(pickle.dumps(response))

            except (socket.error, EOFError, ):
                Log.i("SERVER", f"Player {player_id} from game {game_id} disconnected.")
                if game_id in self.games:
                    self.games.pop(game_id)
                break

        connection.close()


if __name__ == "__main__":
    server = Server()
