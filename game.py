class Game():
    def __init__(self):
        self.stdscr = None
        self.player_list = None

    def change_state(self, state):
        self.state = state

    def update(self):
        self.state.update()


game = Game()
