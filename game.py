import utils
import config
import time
import curses
import select
import random
import json
import multiplayer
from curses.textpad import rectangle


index = 0


start_time = 0
end_time = 0
total_time = 0

total_characters_typed = 0
correct_characters_typed = 0

count = 0

y = 3
x = 3


def score_screen(stdscr):
    accuracy = correct_characters_typed * 100/total_characters_typed
    typing_speed = (correct_characters_typed/5)/(total_time/60)
    utils.clear(stdscr)
    stdscr.addstr(4, 4, "Haha you lost. Your score was: {}".format(count))
    stdscr.addstr(
        6, 4, "Your typing speed was: {:.0f} WPM".format(typing_speed))
    stdscr.addstr(7, 4, "Your accuracy was: {:.2f}%".format(accuracy))

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


def word_finish(stdscr, phrase):
    stdscr.addstr(y + 1, x + 1, phrase, curses.A_NORMAL)
    stdscr.refresh()
    time.sleep(0.1)

    stdscr.addstr(y + 1, x + 1, phrase, curses.A_STANDOUT)
    stdscr.refresh()
    time.sleep(0.1)

    stdscr.addstr(y + 1, x + 1, phrase, curses.A_BOLD)
    stdscr.refresh()
    time.sleep(0.1)


def input_handler(stdscr, phrase):
    global total_characters_typed, correct_characters_typed, start_time, index

    key = stdscr.getch()
    if key == -1:
        return 0

    total_characters_typed += 1

    if key != ord(phrase[index]):
        return 0

    if index == 0:
        start_time = time.time()
    index += 1
    correct_characters_typed += 1

    stdscr.addstr(y + 2, x + 1, " " * index + phrase[index:])

    if multiplayer.lsock:
        utils.send_message(
            multiplayer.lsock, "i" + str(index), encode=True)

    if index >= len(phrase):
        return 1

    stdscr.addstr(y + 2, x + 1 + index, phrase[index], curses.A_UNDERLINE)
    stdscr.refresh()

    return 0


def multiplayer_handler(stdscr, phrase, word_index):

    read_ready, _, _ = select.select([multiplayer.lsock], [], [], 0)

    if read_ready:
        prefix, message = utils.parse_message(multiplayer.lsock)

        if prefix == "f" and message == str(word_index):
            return 1

        elif prefix == "i":
            player = json.loads(message)
            player_index = player["index"]
            if player["id"] != multiplayer.my_id:
                stdscr.addstr(y + 3 + player["id"], x + 1,
                              " " * player_index + phrase[player_index:])
            stdscr.refresh()


def get_word(stdscr):
    if multiplayer.lsock:
        # block until recieve new word
        while True:
            select.select([multiplayer.lsock], [], [])
            prefix, message = utils.parse_message(multiplayer.lsock)
            if prefix == "w":
                current_phrase = message
                break
    else:
        difficulty = 3
        current_phrase = utils.generate_rand_word(difficulty)

    stdscr.addstr(y + 1, x + 1, current_phrase, curses.A_BOLD)
    stdscr.addstr(y + 2, x + 1, current_phrase)

    for conn in multiplayer.players:
        if conn["id"] != multiplayer.my_id:
            stdscr.addstr(y + 3 + conn["id"], x + 1, current_phrase)

    stdscr.refresh()
    return current_phrase


def play(stdscr):
    global index, total_time, total_characters_typed, correct_characters_typed

    utils.clear(stdscr)

    total_time = 0
    total_characters_typed = 0
    correct_characters_typed = 0

    survival(stdscr)

    return score_screen(stdscr)


def survival(stdscr):

    global index, count, total_time

    # settings
    max_time = 20
    bar_width = 50
    finish_bonus = 3

    time_left = max_time
    time_stamp = time.time()

    word_index = 1

    count = 0
    time_taken = 0

    # Keep going until time is left
    while time_left > 0:
        utils.clear(stdscr)
        current_phrase = get_word(stdscr)
        index = 0

        while True:
            time_left -= time.time() - time_stamp
            if time_left <= 0:
                break
            time_stamp = time.time()
            # current_phrase = get_word(stdscr)
            progress = int(time_left/max_time * bar_width)
            # stdscr.addstr(1, 0, str(time_left))
            stdscr.addstr(0, 0, " " * bar_width)
            stdscr.addstr(0, 0, "\u2588" * progress +
                          "\u2591" * (bar_width - progress))
            stdscr.refresh()

            if input_handler(stdscr, current_phrase):
                time_left = min(max_time, time_left + finish_bonus)
                count += 1
                time_taken = time.time() - start_time
                if multiplayer.lsock:
                    utils.send_message(multiplayer.lsock, "f" +
                                       str(time_taken), encode=True)
                break

            if multiplayer.lsock:
                if multiplayer_handler(stdscr, current_phrase, word_index):
                    time_taken = time.time() - start_time
                    break

        word_index += 1
        total_time += time_taken
        word_finish(stdscr, current_phrase)
