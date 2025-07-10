import curses
import multiplayer

from game import game
from utils import SelectScreen

# Bugs:
# When server closes nothing happens to clients - the tcp closes but not udp thread


class TitleState(SelectScreen):
    def __init__(self):
        options = ["Singleplayer",
                   "Multiplayer",
                   "Quit"]

        callbacks = [lambda: game.change_state(None),
                     lambda: game.change_state(
                         multiplayer.MultiplayerMenuState()),
                     lambda: game.change_state(None)]

        super().__init__("Menu", options, callbacks)


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)

    game.stdscr = stdscr
    game.change_state(TitleState())

    while game.state:
        game.update()


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("Keyboard interrupt detected, exiting program")
