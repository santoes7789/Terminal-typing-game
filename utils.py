import curses
import config
import struct
import random
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
            if key in (curses.KEY_RIGHT, curses.KEY_DOWN):
                self.selected = min(len(self.options) - 1, self.selected + 1)
            elif key in (curses.KEY_LEFT, curses.KEY_UP):
                self.selected = max(0, self.selected - 1)
            elif key == 10:
                return self.selected
            self.draw(stdscr)

        return -1


def send_message(lsock, message, encode=False):
    if encode:
        message = message.encode("utf-8")
    msg_length = len(message)

    try:
        lsock.sendall(struct.pack("!I", msg_length) + message)
    except Exception as e:
        raise e


def parse_message(lsock):
    try:
        msg_length = lsock.recv(4)
    except Exception as e:
        raise e

    if not msg_length:
        raise ConnectionResetError

    bytes_to_read = struct.unpack("!I", msg_length)[0]

    try:
        recv_data = lsock.recv(bytes_to_read)
    except Exception as e:
        raise e

    if not recv_data:
        raise ConnectionResetError

    recv_data = recv_data.decode("utf-8")
    prefix = recv_data[0]
    recv_data = recv_data[1:]
    return prefix, recv_data


lines = []
with open("word_bank", "r") as file:
    content = file.read()
sections = content.split("\n\n")
for i in range(len(sections)):
    lines.append(sections[i].split("\n"))


def generate_rand_word(difficulty):
    return random.choice(lines[difficulty]).strip()


def clear(stdscr):
    stdscr.clear()
    rectangle(stdscr,
              config.BORDER, config.BORDER,
              config.SCREEN_HEIGHT - 1 + config.BORDER,
              config.SCREEN_WIDTH - 1 + config.BORDER)
    stdscr.refresh()
