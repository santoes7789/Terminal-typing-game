import curses
import socket
import threading
from queue import Queue

from game import game
from config import TCP_PORT, UDP_PORT

import utils
import main
import random
import time

# until i can be bothered with a proper name input
names = [
    "Tiger", "Eagle", "Wolf", "Falcon", "Dragon", "Panther", "Shark",
    "Fox", "Lion", "Hawk", "Bear", "Snake", "Raven", "Cobra"
]


class Network():
    def initialize(self, ip):
        self.ip = ip

        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.settimeout(5.0)
        self.tcp_sock.connect((ip, TCP_PORT))

        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.connect((ip, 0))  # connect where to get lan ip

        self.recv_queue = Queue()

        self.tcp_thread = threading.Thread(
            target=self.tcp_recv_thread, daemon=True)
        self.tcp_thread.start()

        self.udp_thread = threading.Thread(
            target=self.udp_recv_thread, daemon=True)
        self.udp_thread.start()

    def tcp_recv_thread(self):
        self.tcp_sock.settimeout(None)
        try:
            while True:
                message = utils.receive_tcp(self.tcp_sock)
                utils.debug("(tcp) received :" + str(message))
                self.recv_queue.put(message)
        except Exception as e:
            utils.debug("Error:" + str(e))
            utils.debug("Tcp thread stopping")

    def udp_recv_thread(self):
        try:
            while True:
                message, addr = utils.receive_udp(self.udp_sock)
                utils.debug("(udp) received :" + str(message))
                self.recv_queue.put(message)
        except Exception as e:
            utils.debug("Error:" + str(e))
            utils.debug("Udp thread stopping")

    def send_tcp(self, message):
        utils.send_tcp(self.tcp_sock, message)

    def send_udp(self, message):
        utils.send_udp(self.udp_sock, message, (self.ip, UDP_PORT))

    def disconnect(self):
        self.tcp_sock.shutdown(socket.SHUT_RDWR)
        self.tcp_sock.close()

        self.udp_sock.shutdown(socket.SHUT_RDWR)
        self.udp_sock.close()

        self.udp_thread.join()
        self.tcp_thread.join()


network = Network()


# Asks whether to host or join
class MultiplayerMenuState(utils.SelectScreen):
    def __init__(self):
        options = ["Join",
                   "Host (doesnt work)",
                   "Go back"]

        callbacks = [lambda: game.change_state(IpInputState()),
                     lambda: game.change_state(None),
                     lambda: game.change_state(main.TitleState())]

        super().__init__("Multiplayer", options, callbacks)

    def update(self):
        self.options.update_loop()


# Gets ip address for joining
class IpInputState():
    def __init__(self):
        self.ip = ""
        self.draw()

    def draw(self):
        game.stdscr.clear()
        game.stdscr.addstr(0, 0, "Multiplayer")
        game.stdscr.addstr(2, 3, "Ip Address:")
        game.stdscr.addstr(2, 15, self.ip)
        game.stdscr.refresh()

    def update(self):
        key = game.stdscr.getch()
        if key in (10, 13):
            try:
                network.initialize(self.ip)
                game.change_state(LobbyState())
            except Exception as e:
                game.change_state(utils.PopupState("Could not connect to server",
                                                   main.TitleState))
                utils.debug(str(e))
        elif key != -1:
            if key in (curses.KEY_BACKSPACE, 8):
                self.ip = self.ip[:-1]
            else:
                self.ip += chr(key)

            self.draw()


class LobbyState():
    def __init__(self):
        game.player_name = random.choice(names)
        network.send_tcp(("n", game.player_name))
        network.send_tcp(("a", network.udp_sock.getsockname()))

        options = ["Start game", "Leave lobby"]

        callbacks = [self.start_game, self.leave_lobby]

        self.options = utils.OptionSelect(
            game.stdscr, options, callbacks, 2, 0)

        self.draw()

    def draw(self):
        game.stdscr.clear()
        game.stdscr.addstr(0, 0, "Lobby")
        game.stdscr.addstr(1, 20, "Players:")
        game.stdscr.refresh()
        self.options.draw()

    def update(self):
        self.options.update_loop()
        if not network.recv_queue.empty():
            prefix, content = network.recv_queue.get()
            if prefix == "p":
                self.draw()
                game.player_list = content
                for index, player_data in enumerate(content.values()):
                    game.stdscr.addstr(2 + index, 20, player_data["name"])

            elif prefix == "s":
                game.change_state(utils.PopupState(
                    "Game starting!!", MultiplayerGameState))

    def start_game(self):
        network.send_tcp(("s", ""))

    def leave_lobby(self):
        network.disconnect()
        game.change_state(main.TitleState())


class MultiplayerGameState():
    def __init__(self):
        network.send_tcp(("r", ""))

        self.current_word = ""  # Word player is typing
        self.current_word_index = 1  # Count or index of current word
        self.current_index = 0  # Index of character player is on

        self.finished = True
        self.alive = True

        self.max_time = 10
        self.remaining_time = self.max_time

        # delta time stuff
        self.previous_time = time.time()

        self.draw()

    def draw(self):
        game.stdscr.clear()
        game.stdscr.addstr(0, 0, "Game")

        # print words out
        game.stdscr.addstr(3, 5, game.player_name + ":")
        game.stdscr.addstr(3, 25 + self.current_index,
                           self.current_word[self.current_index:])

        ypos = 1
        for player_data in game.player_list.values():
            if player_data["name"] != game.player_name:
                game.stdscr.addstr(3 + ypos, 5, player_data["name"] + ":")
                game.stdscr.addstr(
                    3 + ypos, 24, str(player_data["word_index"]))
                game.stdscr.addstr(
                    3 + ypos, 25 + player_data["word_index"],
                    self.current_word[player_data["word_index"]:])
                ypos += 1

        game.stdscr.refresh()

    def draw_timer(self):
        if self.remaining_time > 5:
            color = 1
        elif self.remaining_time > 2:
            color = 2
        elif self.remaining_time > 0:
            color = 3
        else:
            color = 4

        game.stdscr.addstr(3, 60, " " * 6)
        game.stdscr.addstr(3, 60, f"{self.remaining_time:.2f}",
                           curses.color_pair(color))

    def update(self):
        key = game.stdscr.getch()

        if not self.finished:
            if key == ord(self.current_word[self.current_index]):
                self.current_index += 1
                self.draw()

                network.send_udp(("i", self.current_index))

                if self.current_index >= len(self.current_word):
                    self.finished = True
                    self.current_word_index += 1
                    network.send_tcp(("r", 1))

        if not network.recv_queue.empty():
            prefix, content = network.recv_queue.get()

            if prefix == "w":

                self.current_word_index, self.current_word = content

                self.finished = False
                self.current_index = 0
                for player_data in game.player_list.values():
                    player_data["word_index"] = 0

                self.draw()

            elif prefix == "i":
                w_index, stuff = content
                if w_index == self.current_word_index:
                    for id, char_index in stuff.items():
                        game.player_list[id]["word_index"] = char_index
                self.draw()

        if self.alive:
            currentTime = time.time()
            deltaTime = currentTime - self.previous_time
            self.previous_time = currentTime

            self.remaining_time -= deltaTime

            if self.remaining_time <= 0:
                self.alive = False
                network.send_tcp(("d", ""))

            self.draw_timer()
