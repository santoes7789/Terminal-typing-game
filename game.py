import utils
import config
import time
import curses
import select
import random
import json
import multiplayer
from curses.textpad import rectangle


typing_speed = 0
index = 0
total_characters_typed = 0
correct_characters_typed = 0
accuracy = 0

y = 3
x = 3


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
    global total_characters_typed, correct_characters_typed
    key = stdscr.getch()
    if key != -1:
        total_characters_typed += 1

    if key == ord(phrase[i]):
        correct_characters_typed += 1
        return 1
    return 0


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
    global total_characters_typed, correct_characters_typed, index

    key = stdscr.getch()
    if key == -1:
        return 0

    total_characters_typed += 1

    if key != ord(phrase[index]):
        return 0

    index += 1
    correct_characters_typed += 1

    stdscr.addstr(y + 2, x + 1, " " * index + phrase[index:])
    stdscr.refresh()

    if multiplayer.lsock:
        utils.send_message(
            multiplayer.lsock, "i" + str(index), encode=True)

    if index >= len(phrase):
        return 1

    return 0


def multiplayer_handler(stdscr, phrase):

    read_ready, _, _ = select.select([multiplayer.lsock], [], [], 0)

    if read_ready:
        prefix, message = utils.parse_message(multiplayer.lsock)

        if prefix == "f":
            return 1

        elif prefix == "i":
            player = json.loads(message)
            player_index = player["index"]
            if player["id"] != multiplayer.my_id:
                stdscr.addstr(y + 3 + player["id"], x + 1,
                              " " * player_index + phrase[player_index:])
            stdscr.refresh()


def play(stdscr):
    global time_taken, index

    count = 0
    time_taken = 0

    # current_phrase = PhraseObject(utils.generate_rand_word(difficulty), 3, 3)
    current_phrase = ""
    while True:

        stdscr.addstr(0, 0, "waiting for word from server... ")
        stdscr.refresh()
        # Get new word
        if multiplayer.lsock:
            # block until recieve new word
            while True:
                select.select([multiplayer.lsock], [], [])
                prefix, message = utils.parse_message(multiplayer.lsock)
                if prefix == "w":
                    current_phrase = message
                    break
        else:

            difficulty = time_trials(count)
            if difficulty == -1:
                break
            current_phrase = get_phrase(difficulty)

        utils.clear(stdscr)
        # Draw phrase
        # rectangle(stdscr, y, x, y + 3, x + len(current_phrase) + 1)
        stdscr.addstr(y + 10, x + 1, "SCORE: " + str(count))
        stdscr.addstr(y + 1, x + 1, current_phrase, curses.A_BOLD)
        stdscr.addstr(y + 2, x + 1, current_phrase)
        for conn in multiplayer.players:
            if conn["id"] != multiplayer.my_id:
                stdscr.addstr(y + 3 + conn["id"], x + 1, current_phrase)

        stdscr.refresh()

        start_time = time.time()

        while True:
            if input_handler(stdscr, current_phrase):
                count += 1
                break

            if multiplayer.lsock:
                if multiplayer_handler(stdscr, current_phrase):
                    break

        index = 0
        end_time = time.time()
        time_taken = end_time - start_time

        if multiplayer.lsock:
            utils.send_message(multiplayer.lsock, "f" +
                               str(time_taken), encode=True)
        word_finish(stdscr, current_phrase)

    return score_screen(stdscr)


def time_trials(count):
    if count < 3:
        return 0
    if count < 10:
        return 1
    elif count < 20:
        return 3
    return -1
