import curses
import config
import struct
from enum import Enum
from curses.textpad import rectangle


class GameState(Enum):
    MAIN_MENU = 1
    PLAY = 2
    EXIT = 3
    LOBBY = 4
    MULTIPLAYER = 5


class Option():
    def __init__(self, x, y, string):
        self.x = x
        self.y = y
        self.string = string


class OptionSelect():
    def __init__(self, stdscr, options, selected=0):
        self.options = options
        self.selected = selected
        self.draw(stdscr)

    def draw(self, stdscr):
        for index, option in enumerate(self.options):
            if index == self.selected:
                format = curses.A_STANDOUT
            else:
                format = curses.A_NORMAL
            stdscr.addstr(option.y, option.x, option.string, format)

    def update_loop(self, stdscr, _key=None):
        if _key:
            key = _key
        else:
            key = stdscr.getch()

        if key != -1:
            if key == curses.KEY_RIGHT or key == curses.KEY_DOWN:
                self.selected = min(len(self.options) - 1, self.selected + 1)
            elif key == curses.KEY_LEFT or key == curses.KEY_UP:
                self.selected = max(0, self.selected - 1)
            elif key == 10 or key == 32:
                return self.selected
            self.draw(stdscr)

        return -1


def send_message(lsock, message):
    msg = message.encode("utf-8")
    msg_length = len(msg)
    lsock.sendall(struct.pack("!I", msg_length) + msg)


def clear(stdscr):
    stdscr.clear()
    rectangle(stdscr,
              config.BORDER, config.BORDER,
              config.SCREEN_HEIGHT - 1 + config.BORDER,
              config.SCREEN_WIDTH - 1 + config.BORDER)
    stdscr.refresh()
