import socket
import pickle


class Network:

    def __init__(self, buffer: int = 2048, port: int = None):
        self.__client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__server = socket.gethostname()
        self.__port = port or 22222
        self.__address = (self.__server, self.__port)
        self.__client_id = None
        self.__buffer = buffer

    @property
    def client_id(self):
        return self.__client_id

    def update_connection(self):
        self.__client_id = pickle.loads(self.__client.recv(self.__buffer))

    def connect(self):
        self.__client.connect(self.__address)

    def send(self, data):
        self.__client.send(pickle.dumps(data))
        return pickle.loads(self.__client.recv(self.__buffer))

    def send_only(self, data):
        self.__client.send(pickle.dumps(data))

    def recv_only(self):
        return pickle.loads(self.__client.recv(self.__buffer))
