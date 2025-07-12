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
        game.my_name = random.choice(names)
        network.send_tcp(("n", game.my_name))
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
            elif prefix == "i":
                game.my_id = content

    def start_game(self):
        network.send_tcp(("s", ""))

    def leave_lobby(self):
        network.disconnect()
        game.change_state(main.TitleState())


class MultiplayerGameState():
    def __init__(self):
        network.send_tcp(("r", None))

        # game settings
        self.max_time = 10
        self.bonus_time = 1

        self.time_taken = 0
        self.current_word = ""  # Word player is typing
        self.current_word_count = 1  # Count or index of current word

        self.finished = True

        for p in game.player_list.values():
            p["remaining_time"] = self.max_time
            p["alive"] = True

        # delta time stuff
        self.previous_time = time.time()

        self.word_win = curses.newwin(len(game.player_list), 35, 3, 5)

        self.draw()

        self.fx = utils.FX()

    def draw(self):
        game.stdscr.clear()
        game.stdscr.addstr(0, 0, "Game")

        self.draw_words()
        self.draw_timer()

        curses.doupdate()

    def draw_words(self):
        self.word_win.clear()

        ypos = 0
        for player_data in game.player_list.values():
            self.word_win.addstr(ypos, 0, player_data["name"] + ":")
            self.word_win.addstr(
                ypos, 20 + player_data["word_index"],
                self.current_word[player_data["word_index"]:])
            ypos += 1

        self.word_win.noutrefresh()

    def draw_timer(self):
        for i, p in enumerate(game.player_list.values()):
            if p["remaining_time"] > 5:
                color = 1
            elif p["remaining_time"] > 2:
                color = 2
            elif p["remaining_time"] > 0:
                color = 3
            else:
                color = 4
            game.stdscr.addstr(3 + i, 60, " " * 5)  # clear the previous text
            game.stdscr.addstr(3 + i, 60, f"{p["remaining_time"]:.2f}",
                               curses.color_pair(color))
        game.stdscr.noutrefresh()

    def update(self):
        currentTime = time.time()
        deltaTime = currentTime - self.previous_time
        self.time_taken += deltaTime
        self.previous_time = currentTime

        key = game.stdscr.getch()

        # update timer:
        for p in game.player_list.values():
            if p["word_index"] < len(self.current_word) and p["alive"]:
                p["remaining_time"] = max(0, p["remaining_time"] - deltaTime)
                self.draw_timer()

        if not self.finished and game.me("alive"):
            if key == ord(self.current_word[game.me("word_index")]):
                game.me()["word_index"] += 1
                curr_i = game.me("word_index")
                self.draw_words()

                network.send_udp(("i", curr_i))

                if curr_i >= len(self.current_word):
                    game.me()["remaining_time"] = min(self.max_time,
                                                      game.me("remaining_time") + self.bonus_time)

                    self.finished = True
                    network.send_tcp(
                        ("r", (game.me("remaining_time"), self.time_taken)))

                    self.fx.add(utils.FXObject_Fade(
                        0.5, 3, 65, f"(+{self.bonus_time:.2f}s)", game.stdscr))

            if game.me("alive") and game.me("remaining_time") <= 0:
                game.me()["alive"] = False
                network.send_tcp(("d", ""))

        if not network.recv_queue.empty():
            prefix, content = network.recv_queue.get()

            if prefix == "w":

                self.current_word_count, self.current_word = content
                self.time_taken = 0

                self.finished = False

                for player_data in game.player_list.values():
                    player_data["word_index"] = 0

                self.draw_words()

            elif prefix == "i":
                w_index, stuff = content
                if w_index == self.current_word_count:
                    for id, char_index in stuff.items():
                        game.player_list[id]["word_index"] = char_index
                self.draw_words()

            elif prefix == "t":
                id, stuff = content
                game.player_list[id]["remaining_time"] = stuff
                self.draw_timer()

            elif prefix == "d":
                game.player_list[content]["remaining_time"] = 0
                game.player_list[content]["alive"] = False

        self.fx.update()
        curses.doupdate()
