import time


class Game():
    def __init__(self):
        self.stdscr = None
        self.player_list = None
        self.my_name = None
        self.my_id = None

        self.phrases = []

        self.player_list = {}

    def change_state(self, state):
        self.state = state

    def update(self):
        self.state.update()

    def me(self, key=None):
        if key:
            return self.player_list[self.my_id][key]
        else:
            return self.player_list[self.my_id]

    def get_accuracy(self):
        total_char = 0
        correct_char = 0
        for p in self.phrases:
            total_char += p.total_char_typed
            correct_char += p.correct_char_typed

        return (correct_char / total_char) * 100

    def get_wpm(self):
        correct_char = 0
        total_time = 0
        for p in self.phrases:
            correct_char += p.correct_char_typed
            total_time += p.time_taken(False)
        return (12 * correct_char) / total_time

    def get_score(self):
        return len(self.phrases)

    def get_avg_reaction(self):
        total_reaction = 0
        for p in self.phrases:
            total_reaction += p.reaction_time()
        return total_reaction/len(self.phrases)


# OK WE MIGHT WANT TO REFRACTOR THIS ENTIRE THING OKAY
class Phrase():
    def __init__(self, phrase):
        self.phrase = phrase
        self.total_char_typed = 0
        self.correct_char_typed = 0
        self.init_time = time.time()
        self.reaction_time_stamp = None
        self.start_time = None

    def finish(self):
        if not self.reaction_time_stamp:
            self.reaction_time_stamp = time.time()
        self.end_time = time.time()

    def type_char(self, key):
        if key != -1:
            if game.me("word_index") == 0:
                self.reaction_time_stamp = time.time()
                self.start_time = time.time()
            self.total_char_typed += 1

            if chr(key) == self.phrase[game.me("word_index")]:
                self.correct_char_typed += 1
                return 1

        return 0

    def reaction_time(self):
        return self.reaction_time_stamp - self.init_time

    def time_taken(self, include_reaction_time=True):
        if include_reaction_time:
            return self.end_time - self.init_time
        else:
            if self.start_time:
                return self.end_time - self.start_time
            else:
                return 0


game = Game()
