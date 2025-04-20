import utils
import curses
from curses.textpad import rectangle
import config
import socket
import select
import json

# When user joins, send neccessary data with it, i.e username
# Possible requests lobby phase:
#  - Retrieve player list
#  - Send message
#  - Start game

# Perhaps make Option have highlight function or something
# Perhaps make a class or fucnion for gather user input, such as ip or name


def join(stdscr, context):

    context.lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    utils.clear(stdscr)

    start_x = config.SCREEN_WIDTH//2 - 15
    stdscr.addstr(11, start_x, "ip address:")

    rectangle(stdscr, 12, start_x, 14, start_x + 30)
    stdscr.refresh()

    ip = ""

    selected = 1

    cancel_btn = utils.Option(start_x, 15, "cancel")
    connect_btn = utils.Option(start_x + 15, 15, "connect")

    option_select = utils.OptionSelect(stdscr,
                                       [cancel_btn, connect_btn], selected=1)

    while True:
        key = stdscr.getch()
        selected = option_select.update_loop(stdscr, _key=key)
        if selected != -1:
            break
        if key != -1 and key != curses.KEY_LEFT and key != curses.KEY_RIGHT:
            if key == curses.KEY_BACKSPACE:
                stdscr.addstr(13, start_x + 1, " " * 29)
                ip = ip[:-1]
            elif chr(key).isnumeric() or chr(key) == ".":
                ip += chr(key)
            stdscr.addstr(13, start_x + 1, ip)
            stdscr.refresh()

    # this is still broken
    if selected:
        context.lsock.connect((ip, config.PORT))
        utils.send_message(context.lsock, "n" +
                           context.player_name, encode=True)
        return utils.GameState.LOBBY
    else:
        context.lsock = None
        return utils.GameState.MAIN_MENU


# I know this is the exact same as the function above but honestly i dont care
def get_username(stdscr, context):
    start_x = config.SCREEN_WIDTH//2 - 15
    stdscr.addstr(11, start_x, "Enter name:")
    rectangle(stdscr, 12, start_x, 14, start_x + 30)
    stdscr.refresh()

    name = ""

    selected = 1

    cancel_btn = utils.Option(start_x, 15, "go back")
    confirm_btn = utils.Option(start_x + 15, 15, "yep i like that name")
    option_select = utils.OptionSelect(
        stdscr, [cancel_btn, confirm_btn], selected=1)

    while True:
        key = stdscr.getch()
        selected = option_select.update_loop(stdscr, _key=key)
        if selected != -1:
            break
        if key != -1 and key != curses.KEY_LEFT and key != curses.KEY_RIGHT:
            if key == curses.KEY_BACKSPACE:
                stdscr.addstr(13, start_x + 1, " " * 29)
                name = name[:-1]
            else:
                name += chr(key)
            stdscr.addstr(13, start_x + 1, name)
            stdscr.refresh()

    if selected:
        context.player_name = name
        return 1
    else:
        return 0


def multiplayer_menu(stdscr, context):

    utils.clear(stdscr)

    if not context.player_name:
        if not get_username(stdscr, context):
            return utils.GameState.MAIN_MENU

    utils.clear(stdscr)

    host_btn = utils.Option(config.SCREEN_WIDTH//2 - 5, 11, "host")
    join_btn = utils.Option(config.SCREEN_WIDTH//2 + 5, 11, "join")
    option_select = utils.OptionSelect(stdscr, [host_btn, join_btn])
    selected = 1

    while True:
        selected = option_select.update_loop(stdscr)

        if selected != -1:
            break

    # join
    if selected == 1:
        return join(stdscr, context)
    elif selected == 0:
        # host
        pass
    return utils.GameState.EXIT


def lobby(stdscr, context):
    context.lsock.setblocking(False)

    utils.clear(stdscr)

    messages = []

    players_win = curses.newwin(
        config.PLAYER_WIN_HEIGHT, config.PLAYER_WIN_WIDTH,
        config.BORDER, config.BORDER)
    players_win.box()
    players_win.refresh()

    chat_win = curses.newwin(
        config.CHAT_WIN_HEIGHT, config.CHAT_WIN_WIDTH,
        config.BORDER, config.PLAYER_WIN_WIDTH + 2)

    msg_box_length = config.CHAT_WIN_WIDTH - 4
    msg = ""
    rectangle(chat_win, config.CHAT_WIN_HEIGHT - 4,
              1, config.CHAT_WIN_HEIGHT - 2, msg_box_length + 2)

    chat_win.box()
    chat_win.refresh()

    settings_win = curses.newwin(
        config.SCREEN_HEIGHT,
        config.SCREEN_WIDTH - config.CHAT_WIN_WIDTH - config.PLAYER_WIN_WIDTH,
        config.BORDER, config.PLAYER_WIN_WIDTH + config.CHAT_WIN_WIDTH + 2)

    settings_win.box()
    settings_win.addstr(1, 1, "start")
    settings_win.refresh()

    active_win = chat_win

    # its messy, but it works
    while True:
        key = stdscr.getch()
        if key != -1:
            if key == curses.KEY_RIGHT:
                active_win = settings_win
                settings_win.addstr(1, 1, "start", curses.A_STANDOUT)
                settings_win.refresh()
            elif key == curses.KEY_LEFT:
                active_win = chat_win
                settings_win.addstr(1, 1, "start", curses.A_NORMAL)
                settings_win.refresh()

            elif active_win == chat_win:
                if key == curses.KEY_BACKSPACE:
                    msg = msg[:-1]
                elif key == 10:
                    utils.send_message(context.lsock, "m" + msg, encode=True)
                    msg = ""
                elif len(msg) < msg_box_length:
                    msg += chr(key)
                chat_win.addstr(config.CHAT_WIN_HEIGHT - 3, 2,
                                " " * msg_box_length)
                chat_win.addstr(config.CHAT_WIN_HEIGHT - 3, 2, msg)
                chat_win.refresh()
            elif active_win == settings_win:
                if key == 10:
                    utils.send_message(context.lsock, "s", encode=True)

        read_ready, _, _ = select.select([context.lsock], [], [], 0)

        if read_ready:
            prefix, recv = utils.parse_message(context.lsock)
            if prefix == "m":
                message = json.loads(recv)

                # find name
                for conn in context.players:
                    if conn["id"] == message["id"]:
                        sender = conn["name"]
                        break

                messages.append(sender + ": " + message["message"])
                if len(messages) > config.PLAYER_WIN_HEIGHT - 2 - 3:
                    messages.pop(0)
                for i, message in enumerate(messages):
                    chat_win.addstr(i + 1, 1, message)
                    chat_win.refresh()
            elif prefix == "p":
                context.players = json.loads(recv)
                for i, name in enumerate(context.players):
                    players_win.addstr(
                        i + 1, 1, name["name"] + "\t" + str(name["id"]))
                    players_win.refresh()
            elif prefix == "s":
                return utils.GameState.PLAY
            elif prefix == "o":
                context.my_id = int(recv)
