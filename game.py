import utils
import config
import time
import curses
import random
import multiplayer
from curses.textpad import rectangle


typing_speed = 0
accuracy = 0


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


def get_phrase(difficulty):
    if multiplayer.lsock:
        pass
    else:
        return utils.generate_rand_word(difficulty)


def check_input(stdscr, phrase, i):
    key = stdscr.getch()
    if key == ord(phrase[i]):
        return 1
    return 0


def play(stdscr):
    utils.clear(stdscr)

    count = 0
    index = 0

    # current_phrase = PhraseObject(utils.generate_rand_word(difficulty), 3, 3)
    current_phrase = ""
    while True:
        if not multiplayer.lsock:
            difficulty = time_trials(count)
            if difficulty == -1:
                break
            current_phrase = get_phrase(difficulty)

        # draw
        y = 3
        x = 3
        rectangle(stdscr, y, x, y + 3, x + len(current_phrase) + 1)
        stdscr.addstr(y + 1, x + 1, current_phrase, curses.A_BOLD)
        stdscr.addstr(y + 2, x + 1, current_phrase)
        stdscr.refresh()

        while True:
            if current_phrase:
                if check_input(stdscr, current_phrase, index):
                    stdscr.addstr(y + 2, x + 1 + index, " ")
                    index += 1
                    if index == len(current_phrase):
                        index = 0
                        count += 1
                        if multiplayer.lsock:
                            utils.send_message(
                                multiplayer.lsock, "w", encode=True)
                        break
                    stdscr.addstr(y + 2, x + 1 + index,
                                  current_phrase[index], curses.A_UNDERLINE)

            if multiplayer.lsock:
                if multiplayer.read_ready:
                    prefix, message = utils.parse_message(multiplayer.lsock)
                    if prefix == "w":
                        current_phrase = message
                        index = 0
                        break

    return score_screen(stdscr)


def time_trials(count):
    if count < 3:
        return 0
    if count < 10:
        return 1
    elif count < 20:
        return 3
    return -1
