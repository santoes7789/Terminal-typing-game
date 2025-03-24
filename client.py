import curses
import time
from enum import Enum
from curses.textpad import rectangle
import random

screen_height = 20
screen_width = 81
border = 2

typing_speed = 0
accuracy = 0


class GameState(Enum):
    MAIN_MENU = 1
    PLAY = 2
    SCORESCREEN = 3
    EXIT = 4


class PhraseObject:
    def __init__(self, phrase, y, x):
        self.phrase = phrase
        self.x = x
        self.y = y

    def draw(self, stdscr):
        rectangle(stdscr, self.y, self.x, self.y +
                  3, self.x + len(self.phrase) + 1)
        stdscr.addstr(self.y + 1, self.x + 1, self.phrase, curses.A_BOLD)
        stdscr.addstr(self.y + 2, self.x + 1, self.phrase)
        stdscr.refresh()

    def type(self, stdscr):
        correct_characters_typed = 0
        total_characters_typed = 0
        start_time = time.time()
        for i in range(0, len(self.phrase)):
            stdscr.addstr(self.y + 2, self.x + i + 1,
                          self.phrase[i], curses.A_UNDERLINE)
            while True:
                key = stdscr.getch()
                if key != -1:
                    total_characters_typed += 1
                    if key == ord(self.phrase[i]):
                        correct_characters_typed += 1
                        stdscr.addstr(self.y + 2, self.x + i + 1, " ")
                        stdscr.refresh()
                        break
        end_time = time.time()

        stdscr.addstr(self.y + 1, self.x + 1, self.phrase, curses.A_REVERSE)
        stdscr.addstr(self.y + 2, self.x + 1, " " *
                      len(self.phrase), curses.A_REVERSE)
        stdscr.refresh()
        time.sleep(0.07)
        stdscr.addstr(self.y + 1, self.x + 1, self.phrase, curses.A_DIM)
        stdscr.addstr(self.y + 2, self.x + 1, " " *
                      len(self.phrase), curses.A_DIM)
        stdscr.refresh()
        time.sleep(0.07)
        stdscr.addstr(self.y + 1, self.x + 1, self.phrase, curses.A_REVERSE)
        stdscr.addstr(self.y + 2, self.x + 1, " " *
                      len(self.phrase), curses.A_REVERSE)
        stdscr.refresh()
        time.sleep(0.07)

        return end_time - start_time, correct_characters_typed, total_characters_typed


def clear(stdscr):
    stdscr.clear()
    rectangle(stdscr,
              border, border,
              screen_height + border, screen_width + border)
    stdscr.refresh()


def main_menu(stdscr):
    clear(stdscr)
    title = "the best typing game"
    stdscr.addstr(12, (screen_width//2 -
                  len(title)//2 + border), title)

    start_text = "play"
    exit_text = "exit"
    selected = 1
    while True:
        stdscr.addstr(15, (screen_width//2 - len(exit_text) //
                      2 - 4 + border), exit_text,
                      curses.A_NORMAL if selected != 0 else curses.A_STANDOUT)
        stdscr.addstr(15, (screen_width//2 - len(start_text) //
                      2 + 4 + border), start_text,
                      curses.A_NORMAL if selected != 1 else curses.A_STANDOUT)
        key = stdscr.getch()
        if key == curses.KEY_LEFT:
            selected = 0
        elif key == curses.KEY_RIGHT:
            selected = 1
        elif key == 10 or key == 32:  # enter or space
            break

    if selected == 1:
        return GameState.PLAY
    elif selected == 0:
        return GameState.EXIT


def score_screen(stdscr):
    clear(stdscr)
    stdscr.addstr(
        4, 4, "Your typing speed was: {:.0f} WPM".format(typing_speed))
    stdscr.addstr(5, 4, "Your accuracy was: {:.2f}%".format(accuracy))

    start_text = "play again"
    exit_text = "main menu"
    selected = 1

    while True:
        stdscr.addstr(15, (screen_width//2 - len(exit_text) //
                      2 - 7 + border), exit_text,
                      curses.A_NORMAL if selected != 0 else curses.A_STANDOUT)
        stdscr.addstr(15, (screen_width//2 - len(start_text) //
                      2 + 7 + border), start_text,
                      curses.A_NORMAL if selected != 1 else curses.A_STANDOUT)
        key = stdscr.getch()
        if key == curses.KEY_LEFT:
            selected = 0
        elif key == curses.KEY_RIGHT:
            selected = 1
        elif key == 10 or key == 32:  # enter or space
            break

    if selected == 1:
        return GameState.PLAY
    else:
        return GameState.MAIN_MENU


def play(stdscr):
    global typing_speed, accuracy
    clear(stdscr)

    lines = []
    with open("word_bank", "r") as file:
        content = file.read()
    sections = content.split("\n\n")
    for i in range(len(sections)):
        lines.append(sections[i].split("\n"))

    time_taken = 0
    correct_characters_typed = 0
    total_characters_typed = 0
    difficulty = 3

    for loop in range(5):
        clear(stdscr)
        phrase = random.choice(lines[difficulty]).strip()
        obj = PhraseObject(phrase, 3, 3)
        obj.draw(stdscr)
        (t, cc, tc) = obj.type(stdscr)
        time_taken += t
        correct_characters_typed += cc
        total_characters_typed += tc

    typing_speed = correct_characters_typed / 5 / \
        (time_taken/60)
    accuracy = correct_characters_typed * 100 / total_characters_typed
    return GameState.SCORESCREEN


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    state = GameState.MAIN_MENU

    while state != GameState.EXIT:
        if state == GameState.MAIN_MENU:
            state = main_menu(stdscr)
        elif state == GameState.PLAY:
            state = play(stdscr)
        elif state == GameState.SCORESCREEN:
            state = score_screen(stdscr)


curses.wrapper(main)
