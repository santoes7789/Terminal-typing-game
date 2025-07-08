import curses
import socket
import threading
from queue import Queue

from game import game
from config import PORT

import utils
import main
import random

# until i can be bothered with a proper name input
names = [
    "Tiger", "Eagle", "Wolf", "Falcon", "Dragon", "Panther", "Shark",
    "Fox", "Lion", "Hawk", "Bear", "Snake", "Raven", "Cobra"
]


# TCP related things
tcp_recv_queue = Queue()
tcp_thread = None


def tcp_recv_thread():
    game.lsock.settimeout(None)
    while True:
        try:
            message = utils.receive_msg(game.lsock)
            tcp_recv_queue.put(message)
        except ConnectionResetError:
            break

    utils.debug("Tcp thread stopping")


def disconnect():
    game.lsock.shutdown(socket.SHUT_RDWR)
    game.lsock.close()
    game.lsock = None
    tcp_thread.join()


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
                game.lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                game.lsock.settimeout(5.0)
                game.lsock.connect((self.ip, PORT))

                global tcp_thread
                tcp_thread = threading.Thread(
                    target=tcp_recv_thread, daemon=True)
                tcp_thread.start()

                game.change_state(LobbyState())
            except Exception as e:
                game.lsock = None
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
        game.name = random.choice(names)
        utils.send_msg(game.lsock, ("n", game.name))

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
        if not tcp_recv_queue.empty():
            prefix, content = tcp_recv_queue.get()

            if prefix == "p":
                self.draw()
                game.player_list = content
                for index, name in enumerate(content.values()):
                    game.stdscr.addstr(2 + index, 20, name)

    def start_game(self):
        utils.send_msg(game.lsock, ("s", ""))

    def leave_lobby(self):
        disconnect()
        game.change_state(main.TitleState())
