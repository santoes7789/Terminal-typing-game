import socket
import selectors

from config import PORT
from utils import send_msg, receive_msg


sel = selectors.DefaultSelector()

players = []

in_lobby = True

next_id = 0


class Client():
    def __init__(self, sock, addr, id):
        # Network
        self.sock = sock
        self.addr = addr

        # Player info
        self.id = id
        self.name = ""

        # Game info
        self.isAlive = True

    def send(self, message):
        send_msg(self.sock, message)
        print("Sent [", message, "] to ", self.addr)

    def read(self):
        try:
            message = receive_msg(self.sock)
            print("receieved [", message, "] from ", self.addr)
            self.manage_request(message)
        except ConnectionResetError:
            self.close()

    def close(self):
        print("Connection closed with client from ", self.addr)

        sel.unregister(self.sock)
        self.sock.close()
        players.remove(self)

    def manage_request(self, message):
        prefix, content = message
        if in_lobby:
            # gives name
            if prefix == "n":
                self.name = content

            # sends message to chat
            elif prefix == "m":
                msg = ("m", {"id": self.id, "message": content})
                broadcast(msg)

            # starts game
            elif prefix == "s":
                msg = ("m", {"id": 0, "message": "GAME STARTING!"})
                broadcast(msg)


def broadcast(message):
    for conn in players:
        conn.send(message)


def accept(sock):
    conn, addr = sock.accept()
    conn.setblocking(False)

    print("Accepted connection from ", addr)

    client_id = generate_id()
    client_obj = Client(conn, addr, client_id)
    players.append(client_obj)

    print("New client given id of :", client_id)

    sel.register(conn, selectors.EVENT_READ, data=client_obj)


def init_server():
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    lsock.bind(("0.0.0.0", PORT))
    lsock.listen()

    lsock.setblocking(False)

    print("Server started!")
    print("Listening on PORT:", PORT)

    sel.register(lsock, selectors.EVENT_READ)


def update_loop():
    while True:
        events = sel.select(timeout=None)
        for key, mask, in events:
            if in_lobby and key.data is None:
                accept(key.fileobj)
            elif key.data:
                key.data.read()


def generate_id():
    global next_id
    next_id += 1
    return next_id


init_server()
update_loop()
