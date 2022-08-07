import pickle
import socket
from _thread import start_new_thread

from bela.game.networking.commands import Commands
from ..main.bela import Bela, GameState
from ..utils.log import Log


class Server:

    def __init__(self):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((socket.gethostname(), 22222))

        self.socket.listen()

        self.buffer = 4096

        self.games = {}
        self.client_id = 0
        self.current_game_id = 0

        Log.i("SERVER", f"Started on port {22222}")

        while True:

            connection, address = self.socket.accept()
            Log.i("SERVER", "Client connected from " + str(address))

            player_id = 0

            self.current_game_id = self.client_id // 4
            self.client_id += 1

            if self.client_id % 4 == 1:
                self.games[self.current_game_id] = Bela(self.current_game_id)
                Log.i("SERVER", "Starting new game | id:" + str(self.current_game_id))
            else:
                player_id = (self.client_id - 1) % 4

            Log.i("SERVER", "New player joined | id:" + str(player_id) + "  | address:" + str(address))
            start_new_thread(self.client, (connection, player_id, self.current_game_id))

    def client(self, connection, player_id, game_id):
        connection.send(pickle.dumps([player_id, game_id]))
        nickname = pickle.loads(connection.recv(self.buffer))

        while True:

            try:
                data = pickle.loads(connection.recv(self.buffer))

                if game_id not in self.games:
                    break

                game = self.games[game_id]
                game.set_nickname(player_id, nickname)

                # Check commands

                if Commands.equals(data, Commands.READY_UP):
                    game.ready_up_player(player_id, True)

                if Commands.equals(data, Commands.PLAY_CARD):
                    if game.get_current_game_state() != GameState.IGRA:
                        passed = False
                    else:
                        passed = game.inspect_played_card(data.data[0].card, player_id)
                    if game.player_turn != player_id:
                        passed = False
                    connection.sendall(pickle.dumps(passed))
                    if passed:
                        game.add_card_to_table(data.data[0], player_id)
                        game.cards[player_id].remove(data.data[0].card)

                if Commands.equals(data, Commands.SWAP_CARDS):
                    game.swap_cards_for_player(player_id, data.data[0])

                if Commands.equals(data, Commands.SORT_CARDS):
                    game.sort_player_cards(player_id)

                if Commands.equals(data, Commands.CALL_ADUT):
                    game.set_adut(data.data[0])
                    game.next_game_state()

                if Commands.equals(data, Commands.DALJE):
                    game.count_dalje += 1
                    game.dalje[player_id] = True
                    game.next_turn()

                if Commands.equals(data, Commands.ZVANJE):
                    game.add_zvanja(data.data[0], player_id)
                    game.zvanje_over[player_id] = True
                    if all(game.zvanje_over):
                        game.next_game_state()

                if Commands.equals(data, Commands.ZVANJE_GOTOVO):
                    game.zvanje_over[player_id] = True
                    if all(game.zvanje_over):
                        game.next_game_state()

                self.games[game_id] = game

                connection.sendall(
                    pickle.dumps(
                        {
                            "game": game,
                        }
                    )
                )

            except (socket.error, EOFError, ):
                Log.i("SERVER", f"Player {player_id} from game {game_id} disconnected.")
                if game_id in self.games:
                    self.games.pop(game_id)
                break

        connection.close()


if __name__ == "__main__":
    server = Server()
