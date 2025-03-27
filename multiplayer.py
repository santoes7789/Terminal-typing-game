import utils
import curses
import config
import socket

lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


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

    ip = "127.0.0.1"
    # join
    if selected == 1:
        try:
            lsock.connect((ip, config.PORT))
            utils.send_message(lsock, config.USERNAME)
        except ConnectionRefusedError:
            return utils.GameState.MAIN_MENU
    elif selected == 0:
        # host
        pass

    return utils.GameState.LOBBY


def lobby(stdscr):

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

    chat_win.box()
    chat_win.refresh()

    try:
        while True:
            data = lsock.recv(1024)
            if data == b"":
                break
            message = data.decode("utf-8")
            messages.append(message)
            if len(messages) > config.PLAYER_WIN_HEIGHT - 2:
                messages.pop(0)
            for i in range(len(messages)):
                chat_win.addstr(i + 1, 1, messages[i])
            chat_win.refresh()
    except KeyboardInterrupt:
        print("\nCaught keyboard interrupt, exiting")
        lsock.close()
    finally:
        print("Closing socket")
        lsock.close()
