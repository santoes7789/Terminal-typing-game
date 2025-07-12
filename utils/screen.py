import curses
import time
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

        self.stdscr.addch(self.choice + 2, self.x + 1, '>')
        self.stdscr.refresh()

    def update_loop(self):

        key = self.stdscr.getch()
        if key != - 1:
            if key == curses.KEY_DOWN:
                self.choice = min(len(self.options) - 1, self.choice + 1)
            elif key == curses.KEY_UP:
                self.choice = max(0, self.choice - 1)
            elif key in (10, 13):
                self.callback[self.choice]()
                return
            for i in range(0, len(self.options)):
                self.stdscr.addch(i + 2, self.x + 1, ' ')

            self.stdscr.addch(self.choice + 2, self.x + 1, '>')


class PopupState():
    def __init__(self, message, new_state):
        self.new_state = new_state

        length = len(message)

        self.win = curses.newwin(5, length + 6, 5, 5)
        self.win.box()
        self.win.addstr(2, 3, message)
        self.win.refresh()

    def clear(self):
        self.win.clear()
        self.win.refresh()
        del self.win

    def update(self):
        time.sleep(2)
        self.clear()
        game.change_state(self.new_state())


def init_colors():
    curses.start_color()

    curses.init_color(0, 0, 0, 0)  # Re-define color 0 as RGB(0,0,0)

    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, 208, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)

    # greyscale pairs for fade effect
    steps = 10
    for i in range(steps):
        grey = int(1000/steps * i)
        curses.init_color(16 + i, grey, grey, grey)
        curses.init_pair(5 + i, 16 + i, curses.COLOR_BLACK)


class FX():
    def __init__(self):
        self.objects = []

    def add(self, obj):
        self.objects.append(obj)

    def update(self):
        for o in self.objects:
            if o.draw():
                self.objects.remove(o)


class FXObject_Fade():
    def __init__(self, duration, y, x, message, stdscr):
        self.time = 0
        self.duration = duration
        self.y = y
        self.x = x
        self.message = message
        self.stdscr = stdscr

        self.previous_time = time.time()

    def draw(self):
        currentTime = time.time()
        deltaTime = currentTime - self.previous_time
        self.previous_time = currentTime

        self.time += deltaTime

        if self.time >= self.duration:
            self.stdscr.addstr(self.y, self.x, " " * len(self.message))
            return 1

        frame = 9 - (int(self.time/self.duration * 10))
        self.stdscr.addstr(self.y, self.x, self.message,
                           curses.color_pair(frame + 5))
        self.stdscr.noutrefresh()
        return 0
