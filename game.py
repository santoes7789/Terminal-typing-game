class Game():
    def change_state(self, state):
        self.state = state

    def update(self):
        self.state.update()


game = Game()
