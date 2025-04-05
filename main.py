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

    start_btn = utils.Option(config.SCREEN_WIDTH//2, 12, "play")
    multiplayer_btn = utils.Option(config.SCREEN_WIDTH//2, 13, "multiplayer")
    exit_btn = utils.Option(config.SCREEN_WIDTH//2, 14, "exit")

    option_select = utils.OptionSelect(stdscr,
                                       [start_btn, multiplayer_btn, exit_btn])

    # this for some reason feels like really bad code
    # but i don't know how else to making it unblocking
    while True:
        selected = option_select.update_loop(stdscr)
        if selected != -1:
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
            state = multiplayer.lobby(stdscr)


try:
    curses.wrapper(main)
except KeyboardInterrupt:
    print("keyboard interrupt detected, program exited")
