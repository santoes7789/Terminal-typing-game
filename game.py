class Game():
    def __init__(self):
        self.stdscr = None
        self.player_list = None
        self.my_name = None
        self.my_id = None

    def change_state(self, state):
        self.state = state

    def update(self):
        self.state.update()

    def me(self, key=None):
        if key:
            return self.player_list[self.my_id][key]
        else:
            return self.player_list[self.my_id]


game = Game()
