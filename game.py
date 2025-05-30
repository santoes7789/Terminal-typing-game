import utils
import config
import time
import curses
import select
import json
from math import ceil
from utils import InGameState

y = 3
x = 3


class Game():
    survival_time = 15
    bonus_time = 2
    bar_width = 50

    def __init__(self, stdscr, context):
        self.context = context
        self.stdscr = stdscr

        self.total_time = 0
        self.total_char_typed = 0
        self.correct_char_typed = 0

        self.phrase_count = 0

        self.curr_phrase = None

        self.score = 0

        self.state = InGameState.NEW_PHRASE

    def accuracy(self):
        if self.total_char_typed == 0:
            return 0
        return self.correct_char_typed/self.total_char_typed * 100

    def typing_speed(self):
        if self.total_time == 0:
            return 0

        return (self.correct_char_typed/5)/(self.total_time/60)

    def get_word(self):
        if self.context.lsock:
            # block until recieve new word
            while True:
                select.select([self.context.lsock], [], [])
                prefix, message = utils.parse_message(self.context.lsock)
                if prefix == "w":
                    current_phrase = message
                    break
        else:
            difficulty = int(min(self.phrase_count/5, utils.word_list_lim))
            current_phrase = utils.generate_rand_word(difficulty)
        for index, item in enumerate(self.context.other_players.items()):
            self.stdscr.addstr(y + 3 + index, x + 1, current_phrase)

        self.phrase_count += 1
        return Phrase(current_phrase, x, y, self.stdscr)

    def input_handler(self):
        key = self.stdscr.getch()
        if key == -1:
            return False

        self.total_char_typed += 1

        if not self.curr_phrase.type_char(chr(key)):
            return False

        self.correct_char_typed += 1

        self.curr_phrase.draw()

        # If it is multiplayer
        if self.context.lsock:
            utils.send_message(self.context.lsock, "i" +
                               str(self.curr_phrase.index), encode=True)

        # If user is finished, return
        if self.curr_phrase.index >= len(self.curr_phrase.phrase):
            return True

        return False

    def multiplayer_handler(self):

        read_ready, _, _ = select.select([self.context.lsock], [], [], 0)

        if read_ready:
            prefix, message = utils.parse_message(self.context.lsock)

            if prefix == "f" and message == str(self.phrase_count):
                self.state = InGameState.NEW_PHRASE

            elif prefix == "i":
                p = json.loads(message)

                # Search
                for i, (id, _) in enumerate(self.context.other_players.items()):
                    if p["id"] == id:
                        self.stdscr.addstr(y + 3 + i,
                                           x + 1,
                                           " " * p["index"] +
                                           self.curr_phrase.phrase[p["index"]:])
                self.stdscr.refresh()

    def timer(self):
        elapsed_time = time.time() - self.last_frame_time
        self.last_frame_time = time.time()
        self.time_left -= elapsed_time
        self.time_left = max(0, self.time_left)

        progress = ceil(
            (self.time_left/self.survival_time * self.bar_width))

        self.stdscr.addstr(0, 0, "\u2591" * self.bar_width)
        self.stdscr.addstr(0, 0, "\u2588" * progress)

        self.stdscr.refresh()

    def add_time(self, add):

        curr_progress = ceil(
            (self.time_left/self.survival_time * self.bar_width))

        self.time_left = min(self.time_left + add, self.survival_time)

        added_progress = ceil(
            (self.time_left/self.survival_time * self.bar_width))

        self.stdscr.addstr(0, 0, "\u2591" * self.bar_width)
        self.stdscr.addstr(0, 0, "\u2592" * added_progress)
        self.stdscr.addstr(0, 0, "\u2588" * curr_progress)
        self.stdscr.refresh()

    def typing(self):
        self.timer()
        # When user finishes word
        if self.input_handler():
            # Add bonus time
            self.add_time(self.bonus_time)

            # Add time to total time taken
            self.total_time += time.time() - self.word_start_time

            # Flash word
            self.curr_phrase.word_finish()

            self.state = InGameState.FINISHED

    def finished_phrase(self):
        if not self.context.lsock:
            self.state = InGameState.NEW_PHRASE

    def new_phrase(self):
        utils.clear(self.stdscr)
        self.curr_phrase = self.get_word()
        self.word_start_time = time.time()
        self.last_frame_time = time.time()
        self.state = InGameState.TYPING

    def survival(self):
        self.time_left = self.survival_time

        state_handlers = {
            InGameState.TYPING: self.typing,
            InGameState.NEW_PHRASE: self.new_phrase,
            InGameState.FINISHED: self.finished_phrase
        }

        # Surely theres a better way to do all this
        while self.state != InGameState.DONE:
            state_handlers[self.state]()

            if self.context.lsock:
                self.multiplayer_handler()

            else:
                if self.time_left <= 0:
                    self.state = InGameState.DONE
                    break


class Phrase():
    def __init__(self, phrase, x, y, stdscr):
        self.phrase = phrase
        self.index = 0
        self.start_time = time.time()

        self.x = x
        self.y = y

        self.stdscr = stdscr

        stdscr.addstr(y + 1, x + 1, phrase, curses.A_BOLD)
        stdscr.addstr(y + 2, x + 1, phrase)
        stdscr.refresh()

    def type_char(self, char):
        if char == self.curr_char():
            self.index += 1
            return True
        return False

    def curr_char(self):
        return self.phrase[self.index]

    def draw(self):
        self.stdscr.addstr(self.y + 2, self.x + 1, " " * self.index +
                           self.phrase[self.index:])
        if self.index < len(self.phrase):
            self.stdscr.addstr(self.y + 2, self.x + 1 + self.index,
                               self.phrase[self.index], curses.A_UNDERLINE)
        self.stdscr.refresh()

    def word_finish(self):
        self.stdscr.addstr(y + 1, x + 1, self.phrase, curses.A_NORMAL)
        self.stdscr.refresh()
        time.sleep(0.1)

        self.stdscr.addstr(y + 1, x + 1, self.phrase, curses.A_STANDOUT)
        self.stdscr.refresh()
        time.sleep(0.1)

        self.stdscr.addstr(y + 1, x + 1, self.phrase, curses.A_BOLD)
        self.stdscr.refresh()
        time.sleep(0.1)


def score_screen(stdscr, game):
    utils.clear(stdscr)
    stdscr.addstr(
        4, 4, "Haha you lost. Your score was: {}".format(game.score))
    stdscr.addstr(6, 4, "Your typing speed was: {:.0f} WPM".format(
        game.typing_speed()))
    stdscr.addstr(7, 4, "Your accuracy was: {:.2f}%".format(game.accuracy()))

    start_btn = utils.Option(30, config.SCREEN_HEIGHT//2, "play again")
    exit_btn = utils.Option(5, config.SCREEN_HEIGHT//2, "main menu")

    option_select = utils.OptionSelect(
        stdscr, [exit_btn, start_btn], selected=1)

    while True:
        selected = option_select.update_loop(stdscr)
        if selected != -1:
            break

    if selected == 1:
        return utils.GameState.PLAY
    else:
        return utils.GameState.MAIN_MENU


def play(stdscr, context):
    utils.clear(stdscr)
    game = Game(stdscr, context)
    game.survival()
    return score_screen(stdscr, game)
