import utils
import config

import time
import curses
import random
from curses.textpad import rectangle


typing_speed = 0
accuracy = 0


class PhraseObject:
    def __init__(self, phrase, y, x):
        self.phrase = phrase
        self.x = x
        self.y = y
        self.index = 0
        self.correct_characters_typed = 0
        self.total_characters_typed = 0

        self.blink = False
        self.finished = False

        self.time = 0
        self.lasttime = time.time()

    def draw(self, stdscr):
        rectangle(stdscr, self.y, self.x, self.y +
                  3, self.x + len(self.phrase) + 1)
        stdscr.addstr(self.y + 1, self.x + 1, self.phrase, curses.A_BOLD)
        stdscr.addstr(self.y + 2, self.x + 1, self.phrase)
        stdscr.refresh()

    def anim_finish(self, stdscr):
        self.time += time.time() - self.lasttime
        self.lasttime = time.time()
        stdscr.refresh()
        if self.time < 0.07:
            stdscr.addstr(self.y + 1, self.x + 1,
                          self.phrase, curses.A_REVERSE)
            stdscr.addstr(self.y + 2, self.x + 1, " " *
                          len(self.phrase), curses.A_REVERSE)
            return 0
        elif self.time < 0.14:
            stdscr.addstr(self.y + 1, self.x + 1, self.phrase, curses.A_DIM)
            stdscr.addstr(self.y + 2, self.x + 1, " " *
                          len(self.phrase), curses.A_DIM)
            return 0
        elif self.time < 0.21:
            stdscr.addstr(self.y + 1, self.x + 1,
                          self.phrase, curses.A_REVERSE)
            stdscr.addstr(self.y + 2, self.x + 1, " " *
                          len(self.phrase), curses.A_REVERSE)
            return 0
        elif self.time < 0.28:
            return 1
        return 0

    def update(self, stdscr):
        if not self.finished:
            key = stdscr.getch()
            if key != -1:
                self.total_characters_typed += 1
                if key == ord(self.phrase[self.index]):
                    self.correct_characters_typed += 1
                    stdscr.addstr(self.y + 2, self.x + self.index + 1, " ")
                    self.index += 1
                    if self.index == len(self.phrase):
                        self.finished = True
                        self.lasttime = time.time()
                    else:
                        stdscr.addstr(self.y + 2, self.x + self.index + 1,
                                      self.phrase[self.index], curses.A_UNDERLINE)
            return 0
        else:
            return self.anim_finish(stdscr)


def score_screen(stdscr):
    utils.clear(stdscr)
    stdscr.addstr(
        4, 4, "Your typing speed was: {:.0f} WPM".format(typing_speed))
    stdscr.addstr(5, 4, "Your accuracy was: {:.2f}%".format(accuracy))

    start_btn = utils.Option(30, config.SCREEN_HEIGHT//2, "play again")
    exit_btn = utils.Option(5, config.SCREEN_HEIGHT//2, "main menu")

    option_select = utils.OptionSelect(stdscr,
                                       [exit_btn, start_btn],
                                       selected=1)
    while True:
        selected = option_select.update_loop(stdscr)
        if selected != -1:
            break

    if selected == 1:
        return utils.GameState.PLAY
    else:
        return utils.GameState.MAIN_MENU


def play(stdscr):
    utils.clear(stdscr)

    lines = []
    with open("word_bank", "r") as file:
        content = file.read()
    sections = content.split("\n\n")
    for i in range(len(sections)):
        lines.append(sections[i].split("\n"))

    difficulty = 3
    count = 0

    phrase = random.choice(lines[difficulty]).strip()
    current_phrase = PhraseObject(phrase, 3, 3)
    current_phrase.draw(stdscr)

    while True:
        if current_phrase.update(stdscr):
            count += 1
            if count > 2:
                break
            phrase = random.choice(lines[difficulty]).strip()
            current_phrase = PhraseObject(phrase, 3, 3)
            current_phrase.draw(stdscr)

    return score_screen(stdscr)
