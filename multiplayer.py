import main
import curses
import socket

from game import game
from utils import SelectScreen, PopupState, OptionSelect
from config import PORT


# Asks whether to host or join
class MultiplayerMenuState(SelectScreen):
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
        game.stdscr.clear()
        game.stdscr.addstr(0, 0, "Multiplayer")

        game.stdscr.addstr(2, 3, "Ip Address:")
        game.stdscr.refresh()
        self.ip = ""

    def update(self):
        key = game.stdscr.getch()
        if key in (10, 13):
            try:
                game.lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                game.lsock.settimeout(5.0)
                game.lsock.connect((self.ip, PORT))
                game.change_state(LobbyState())
            except Exception:
                game.lsock = None
                game.change_state(PopupState("Could not connect to server",
                                             main.TitleState))
        elif key != -1:
            game.stdscr.addstr(2, 15, " " * len(self.ip))

            if key in (curses.KEY_BACKSPACE, 8):
                self.ip = self.ip[:-1]
            else:
                self.ip += chr(key)
            game.stdscr.addstr(2, 15, self.ip)


class LobbyState():
    def __init__(self):
        game.stdscr.clear()
        game.stdscr.addstr(0, 0, "Lobby")
        game.stdscr.refresh()

        options = ["Start game", "Leave lobby"]

        callbacks = [lambda: game.change_state(IpInputState()),
                     lambda: game.change_state(main.TitleState())]
        self.options = OptionSelect(game.stdscr, options, callbacks, 2, 7)

    def update(self):
        self.options.update_loop()
