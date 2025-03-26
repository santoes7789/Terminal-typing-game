import config
from enum import Enum
from curses.textpad import rectangle


class GameState(Enum):
    MAIN_MENU = 1
    PLAY = 2
    EXIT = 3


def clear(stdscr):
    stdscr.clear()
    rectangle(stdscr,
              config.BORDER, config.BORDER,
              config.SCREEN_HEIGHT + config.BORDER,
              config.SCREEN_WIDTH + config.BORDER)
    stdscr.refresh()
