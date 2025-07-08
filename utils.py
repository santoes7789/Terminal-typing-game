import curses
import pickle
from game import game


class SelectScreen():
    def __init__(self, title, options, callbacks):
        game.stdscr.clear()
        game.stdscr.addstr(0, 0, title)
        game.stdscr.refresh()

        self.options = OptionSelect(game.stdscr, options, callbacks, 2, 0)

    def update(self):
        self.options.update_loop()


class OptionSelect():
    def __init__(self, stdscr, options, callback, y, x):
        self.stdscr = stdscr

        self.options = options
        self.callback = callback

        self.x = x
        self.y = y

        self.choice = 0

        self.draw()

    def draw(self):
        for index, text in enumerate(self.options):
            self.stdscr.addstr(index + self.y, 3 + self.x, text)

    def update_loop(self):

        key = self.stdscr.getch()
        if key == curses.KEY_DOWN:
            self.choice = min(len(self.options) - 1, self.choice + 1)
        elif key == curses.KEY_UP:
            self.choice = max(0, self.choice - 1)
        elif key in (10, 13):
            self.callback[self.choice]()
            return

        # Update screen
        for i in range(2, 5):
            self.stdscr.addch(i, self.x + 1, ' ')

        self.stdscr.addch(self.choice + 2, self.x + 1, '>')
        self.stdscr.refresh()


class PopupState():
    def __init__(self, message, new_state):
        self.new_state = new_state

        length = len(message)

        self.win = curses.newwin(5, length + 6, 5, 5)
        self.win.box()
        self.win.addstr(2, 3, message)
        self.win.refresh()

    def update(self):
        if self.win.getch():
            self.win.clear()
            self.win.refresh()
            del self.win
            game.change_state(self.new_state())


def send_msg(lsock, message):
    message = pickle.dumps(message)

    msg_length = len(message)

    lsock.sendall(msg_length.to_bytes(4, "big") + message)


def receive_msg(lsock):
    msg_length = lsock.recv(4)

    if not msg_length:
        raise ConnectionResetError

    bytes_to_read = int.from_bytes(msg_length, "big")

    recv_data = lsock.recv(bytes_to_read)

    if not recv_data:
        raise ConnectionResetError

    recv_data = pickle.loads(recv_data)
    return recv_data
