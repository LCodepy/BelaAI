import socket
import pickle


class Network:

    def __init__(self, buffer: int = 2048):
        self.__client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__server = socket.gethostname()
        self.__port = 22222
        self.__address = (self.__server, self.__port)
        self.__player_id = None
        self.__game_id = None
        self.__buffer = buffer

    @property
    def player_id(self):
        return self.__player_id

    @property
    def game_id(self):
        return self.__game_id

    def update_connection(self):
        self.__player_id, self.__game_id = pickle.loads(self.__client.recv(self.__buffer))

    def connect(self):
        self.__client.connect(self.__address)

    def send(self, data):
        self.__client.send(pickle.dumps(data))
        return pickle.loads(self.__client.recv(self.__buffer))

    def send_only(self, data):
        self.__client.send(pickle.dumps(data))

    def recv_only(self):
        return pickle.loads(self.__client.recv(self.__buffer))
