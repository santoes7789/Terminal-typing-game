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
