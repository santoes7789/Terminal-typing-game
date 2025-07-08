import socket
import selectors
import random

from config import PORT
from utils import send_tcp, receive_tcp


sel = selectors.DefaultSelector()

players = []

in_lobby = True

next_id = 0

# will delete later and use word bank but this is fine for now
word_bank = [
    "cat", "umbrella", "zebra", "quantum", "sky", "incredible", "do", "pixel",
    "fluctuate", "eagle", "zen", "mythology", "blip", "serendipity", "on",
    "wander", "crimson", "go", "reverberation", "elm"
]


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
        self.ready = False  # ready for next word

    def send(self, message):
        send_tcp(self.sock, message)
        print("Sent [", message, "] to ", self.addr)

    def read(self):
        try:
            message = receive_tcp(self.sock)
            print("receieved [", message, "] from ", self.addr)
            self.manage_request(message)
        except ConnectionResetError:
            self.close()

    def close(self):
        print("Connection closed with client from ", self.addr)

        players.remove(self)
        send_player_list()

        sel.unregister(self.sock)
        self.sock.close()

    def manage_request(self, message):
        prefix, content = message

        global in_lobby
        if in_lobby:
            # gives name, sends complete player list to all
            if prefix == "n":
                self.name = content
                send_player_list()

            # sends message to chat
            elif prefix == "m":
                msg = ("m", {"id": self.id, "message": content})
                broadcast(msg)

            # starts game
            elif prefix == "s":
                msg = ("s", "")
                broadcast(msg)
                in_lobby = False
                print("GAME STARTED")
        else:
            # check if all players are ready
            if prefix == "r":
                self.ready = True

                if all(player.ready for player in players):
                    send_new_word()


def broadcast(message):
    for conn in players:
        conn.send(message)


def send_player_list():
    player_dict = {}
    for conn in players:
        player_dict[conn.id] = conn.name

    msg = ("p", player_dict)
    broadcast(msg)


def send_new_word():
    word = random.choice(word_bank)
    msg = ("w", word)
    broadcast(msg)


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
