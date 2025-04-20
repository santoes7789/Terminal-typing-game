import curses
import game
import multiplayer
import utils
import config


def main_menu(stdscr, context):
    utils.clear(stdscr)

    middle = config.SCREEN_WIDTH//2

    title = "the best typing game"

    stdscr.addstr(9, (middle -
                  len(title)//2 + config.BORDER), title)

    start_btn = utils.Option(middle, 12, "play")
    multiplayer_btn = utils.Option(middle, 13, "multiplayer")
    exit_btn = utils.Option(middle, 14, "exit")
    option_select = utils.OptionSelect(stdscr,
                                       [start_btn, multiplayer_btn, exit_btn])
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

    state_handlers = {
        utils.GameState.MAIN_MENU: main_menu,
        utils.GameState.PLAY: game.play,
        utils.GameState.MULTIPLAYER: multiplayer.multiplayer_menu,
        utils.GameState.LOBBY: multiplayer.lobby, }

    context = utils.Context()

    while state != utils.GameState.EXIT:
        handler = state_handlers.get(state)
        state = handler(stdscr, context)


try:
    curses.wrapper(main)
except KeyboardInterrupt:
    print("keyboard interrupt detected, program exited")
