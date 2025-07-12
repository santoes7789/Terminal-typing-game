import socket
import selectors
import random

from config import TCP_PORT, UDP_PORT
from utils import send_tcp, receive_tcp, send_udp, receive_udp

import time


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


class GameData():
    def __init__(self):
        self.word_count = 0


game = GameData()


class Client():
    def __init__(self, sock, addr, id):
        # Network
        self.sock = sock
        self.addr = addr
        self.udp_addr = ()

        # Player info
        self.id = id
        self.name = ""

        # Game info
        self.alive = True
        self.ready = False  # ready for next word
        self.char_index = 0

    def send(self, message, debug=True):
        send_tcp(self.sock, message)
        if debug:
            print("(tcp) Sent", message, "to", self.addr)

    def read(self):
        try:
            message = receive_tcp(self.sock)
            print("(tcp) receieved", message, "from", self.addr)
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
                self.send(("i", self.id))
                send_player_list()

            # gives udp address
            elif prefix == "a":
                self.udp_addr = content

            # sends message to chat
            elif prefix == "m":
                msg = ("m", {"id": self.id, "message": content})
                broadcast_tcp(msg)

            # starts game
            elif prefix == "s":
                msg = ("s", "")
                broadcast_tcp(msg)
                in_lobby = False
                print("GAME STARTED")

        else:
            # check if all players are ready for new word
            # triggered when they finish word
            if prefix == "r":
                self.ready = True

                if content:
                    t_remaining, t_taken = content

                    broadcast_tcp(("t", (self.id, t_remaining)))

                if all(not p.alive for p in players):
                    pass
                if all(p.ready for p in players if p.alive):
                    send_new_word()

            elif prefix == "d":
                self.alive = False

                broadcast_tcp(("d", self.id))

                if all(not p.alive for p in players):
                    pass
                elif all(p.ready for p in players if p.alive):
                    send_new_word()


def broadcast_tcp(message):
    for p in players:
        p.send(message, debug=False)

    print("(tcp) broadcast ", message)


def send_player_list():
    player_dict = {}
    for p in players:
        player_dict[p.id] = {"name": p.name, "word_index": 0}

    msg = ("p", player_dict)
    broadcast_tcp(msg)


def send_new_word():
    word = random.choice(word_bank)
    game.word_count += 1
    msg = ("w", (game.word_count, word))
    broadcast_tcp(msg)

    for p in players:
        p.char_index = 0
        p.ready = False


def accept(sock):
    conn, addr = sock.accept()
    conn.setblocking(False)

    print("Accepted connection from ", addr)

    client_id = generate_id()
    client_obj = Client(conn, addr, client_id)
    players.append(client_obj)

    print("New client given id of :", client_id)

    sel.register(conn, selectors.EVENT_READ, data=client_obj)


def broadcast_udp(message):
    for p in players:
        send_udp(udp_sock, message, p.udp_addr)

    print("(tcp) broadcast ", message)


def process_udp(data, addr):
    prefix, content = data

    if prefix == "i":
        # create list
        player_index_list = {}
        for p in players:
            if p.udp_addr == addr:
                p.char_index = content
            player_index_list[p.id] = p.char_index

        broadcast_udp(("i", (game.word_count, player_index_list)))


def init_tcp_server():
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_sock.bind(("0.0.0.0", TCP_PORT))
    tcp_sock.listen()

    tcp_sock.setblocking(False)

    print("TCP Server started!")
    print("Listening for TCP on PORT:", TCP_PORT)

    sel.register(tcp_sock, selectors.EVENT_READ)
    return tcp_sock


def init_udp_server():
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(("0.0.0.0", UDP_PORT))

    udp_sock.setblocking(False)

    print("UDP Server started!")
    print("Listening for UDP on PORT:", UDP_PORT)

    sel.register(udp_sock, selectors.EVENT_READ)
    return udp_sock


def update_loop():
    while True:
        events = sel.select(timeout=None)
        for key, mask, in events:
            # new connection
            if key.fileobj is tcp_sock and in_lobby:
                accept(tcp_sock)

            # udp client message
            elif key.fileobj is udp_sock:
                data, addr = receive_udp(udp_sock)
                print("(udp) receieved", data, "from ", addr)
                process_udp(data, addr)

            # tcp client message
            else:
                key.data.read()


def generate_id():
    global next_id
    next_id += 1
    return next_id


tcp_sock = init_tcp_server()
udp_sock = init_udp_server()
update_loop()
