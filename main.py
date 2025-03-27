import curses
import game
import multiplayer
import utils
import config


def main_menu(stdscr):
    utils.clear(stdscr)
    title = "the best typing game"
    stdscr.addstr(9, (config.SCREEN_WIDTH//2 -
                  len(title)//2 + config.BORDER), title)

    start_text = "play"
    exit_text = "exit"
    multiplayer_text = "multiplayer"
    selected = 1

    while True:
        stdscr.addstr(12, (config.SCREEN_WIDTH//2-len(start_text)//2) + config.BORDER,
                      start_text, curses.A_STANDOUT if selected == 0 else curses.A_NORMAL)
        stdscr.addstr(13, (config.SCREEN_WIDTH//2-len(multiplayer_text)//2) + config.BORDER,
                      multiplayer_text, curses.A_STANDOUT if selected == 1 else curses.A_NORMAL)
        stdscr.addstr(14, (config.SCREEN_WIDTH//2-len(exit_text)//2) + config.BORDER,
                      exit_text, curses.A_STANDOUT if selected == 2 else curses.A_NORMAL)
        key = stdscr.getch()

        if key == curses.KEY_DOWN:
            selected = min(2, selected + 1)
        elif key == curses.KEY_UP:
            selected = max(0, selected - 1)
        elif key == 10 or key == 32:  # enter or space
            break

    if selected == 0:
        return utils.GameState.PLAY
    elif selected == 1:
        return utils.GameState.MULTIPLAYER
    elif selected == 2:
        return utils.GameState.EXIT


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    state = utils.GameState.MAIN_MENU

    while state != utils.GameState.EXIT:
        if state == utils.GameState.MAIN_MENU:
            state = main_menu(stdscr)
        elif state == utils.GameState.PLAY:
            state = game.play(stdscr)
        elif state == utils.GameState.MULTIPLAYER:
            state = multiplayer.multiplayer_menu(stdscr)
        elif state == utils.GameState.LOBBY:
            state == multiplayer.lobby(stdscr)


curses.wrapper(main)
