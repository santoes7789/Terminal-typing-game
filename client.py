import curses
import game
import utils
import config


def main_menu(stdscr):
    utils.clear(stdscr)
    title = "the best typing game"
    stdscr.addstr(12, (config.SCREEN_WIDTH//2 -
                  len(title)//2 + config.BORDER), title)

    start_text = "play"
    exit_text = "exit"
    selected = 1

    while True:
        stdscr.addstr(15, (config.SCREEN_WIDTH//2 - len(exit_text) //
                      2 - 4 + config.BORDER), exit_text,
                      curses.A_NORMAL if selected != 0 else curses.A_STANDOUT)
        stdscr.addstr(15, (config.SCREEN_WIDTH//2 - len(start_text) //
                      2 + 4 + config.BORDER), start_text,
                      curses.A_NORMAL if selected != 1 else curses.A_STANDOUT)
        key = stdscr.getch()

        if key == curses.KEY_LEFT:
            selected = 0
        elif key == curses.KEY_RIGHT:
            selected = 1
        elif key == 10 or key == 32:  # enter or space
            break

    if selected == 1:
        return utils.GameState.PLAY
    elif selected == 0:
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


curses.wrapper(main)
