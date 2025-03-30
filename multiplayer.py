import utils
import curses
from curses.textpad import rectangle
import config
import socket
import select

lsock = None

# When user joins, send neccessary data with it, i.e username
# Possible requests lobby phase:
#  - Retrieve player list
#  - Send message


def join(stdscr):

    global lsock
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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
                stdscr.addstr(13, start_x + 1, " " * 30)
                ip = ip[:-1]
            elif chr(key).isnumeric() or chr(key) == ".":
                ip += chr(key)
            stdscr.addstr(13, start_x + 1, ip)
            stdscr.refresh()

    # this is still broken
    if selected:
        try:
            lsock.connect((ip, config.PORT))
        except Exception:
            return utils.GameState.MAIN_MENU

        utils.send_message(lsock, "n" + config.USERNAME, encode=True)
        return utils.GameState.LOBBY
    else:
        return utils.GameState.MAIN_MENU


def multiplayer_menu(stdscr):
    utils.clear(stdscr)
    host_text = "host"
    join_text = "join"
    selected = 1

    while True:
        stdscr.addstr(11, (config.SCREEN_WIDTH//2 - len(host_text) //
                      2 - 4 + config.BORDER), host_text,
                      curses.A_STANDOUT if selected == 0 else curses.A_NORMAL)
        stdscr.addstr(11, (config.SCREEN_WIDTH//2 - len(join_text) //
                      2 + 4 + config.BORDER), join_text,
                      curses.A_STANDOUT if selected == 1 else curses.A_NORMAL)

        key = stdscr.getch()

        if key == curses.KEY_LEFT:
            selected = 0
        elif key == curses.KEY_RIGHT:
            selected = 1
        elif key == 10 or key == 32:  # enter or space
            break

    # join
    if selected == 1:
        return join(stdscr)
    elif selected == 0:
        # host
        pass
    return utils.GameState.EXIT


def lobby(stdscr):

    lsock.setblocking(False)

    utils.clear(stdscr)

    players = []
    messages = []

    players_win = curses.newwin(
        config.PLAYER_WIN_HEIGHT, config.PLAYER_WIN_WIDTH,
        config.BORDER, config.BORDER)
    players_win.box()
    players_win.refresh()

    chat_win = curses.newwin(
        config.CHAT_WIN_HEIGHT, config.CHAT_WIN_WIDTH,
        config.BORDER, config.PLAYER_WIN_WIDTH + 1)

    msg_box_length = config.CHAT_WIN_WIDTH - 4
    msg = ""
    rectangle(chat_win, config.CHAT_WIN_HEIGHT - 4,
              1, config.CHAT_WIN_HEIGHT - 2, msg_box_length + 2)

    chat_win.keypad(True)
    chat_win.nodelay(True)
    chat_win.box()
    chat_win.refresh()

    utils.send_message(lsock, "p", encode=True)

    while True:
        key = chat_win.getch()
        if key != -1:
            if key == curses.KEY_BACKSPACE:
                msg = msg[:-1]
            elif key == 10:
                utils.send_message(lsock, "m" + msg, encode=True)
                msg = ""
            elif len(msg) < msg_box_length:
                msg += chr(key)
            chat_win.addstr(config.CHAT_WIN_HEIGHT - 3, 2,
                            " " * msg_box_length)
            chat_win.addstr(config.CHAT_WIN_HEIGHT - 3, 2, msg)

        read_ready, _, _ = select.select([lsock], [], [], 0)

        if read_ready:
            try:
                prefx, recv = utils.parse_message(lsock)
            except Exception:
                return utils.GameState.MAIN_MENU

            if prefx == "m":
                messages.append(recv)
                if len(messages) > config.PLAYER_WIN_HEIGHT - 2 - 3:
                    messages.pop(0)
                for i, message in enumerate(messages):
                    chat_win.addstr(i + 1, 1, message)
                    chat_win.refresh()
            elif prefx == "p":
                players = recv.split("\n")
                for i, name in enumerate(players):
                    players_win.addstr(i + 1, 1, name)
                    players_win.refresh()
