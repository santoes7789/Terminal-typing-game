import curses

from game import game, Phrase

from utils import screen, network, helpers
import main
import random
import time

# until i can be bothered with a proper name input
names = [
    "Tiger", "Eagle", "Wolf", "Falcon", "Dragon", "Panther", "Shark",
    "Fox", "Lion", "Hawk", "Bear", "Snake", "Raven", "Cobra"
]


network_obj = network.Network()


# Asks whether to host or join
class MultiplayerMenuState(screen.SelectScreen):
    def __init__(self):
        options = ["Join",
                   "Host (doesnt work)",
                   "Go back"]

        callbacks = [lambda: game.change_state(IpInputState()),
                     lambda: game.change_state(None),
                     lambda: game.change_state(main.TitleState())]

        super().__init__("Multiplayer", options, callbacks)

    def update(self):
        self.options.update_loop()


# Gets ip address for joining
class IpInputState():
    def __init__(self):
        self.ip = ""
        self.draw()

    def draw(self):
        game.stdscr.clear()
        game.stdscr.addstr(0, 0, "Multiplayer")
        game.stdscr.addstr(2, 3, "Ip Address:")
        game.stdscr.addstr(2, 15, self.ip)
        game.stdscr.refresh()

    def update(self):
        key = game.stdscr.getch()
        if key in (10, 13):
            try:
                game.my_name = random.choice(names)
                network_obj.initialize(self.ip, game.my_name)
                game.change_state(LobbyState())
            except Exception as e:
                game.change_state(screen.PopupState("Could not connect to server",
                                                    main.TitleState))
                helpers.debug(str(e))
        elif key != -1:
            if key in (curses.KEY_BACKSPACE, 8):
                self.ip = self.ip[:-1]
            else:
                self.ip += chr(key)

            self.draw()


class LobbyState():
    def __init__(self):

        options = ["Start game", "Leave lobby"]

        callbacks = [self.start_game, self.leave_lobby]

        self.options = screen.OptionSelect(
            game.stdscr, options, callbacks, 2, 0)

        self.draw()

    def draw(self):
        game.stdscr.clear()
        game.stdscr.addstr(0, 0, "Lobby")
        game.stdscr.addstr(1, 20, "Players:")

        for index, player_data in enumerate(game.player_list.values()):
            game.stdscr.addstr(2 + index, 20, player_data["name"])

        game.stdscr.refresh()
        self.options.draw()

    def update(self):
        self.options.update_loop()
        if not network_obj.recv_queue.empty():
            prefix, content = network_obj.recv_queue.get()
            if prefix == "p":
                game.player_list = content
                self.draw()

            elif prefix == "s":
                game.change_state(screen.PopupState(
                    "Game starting!!", MultiplayerGameState))
            elif prefix == "i":
                game.my_id = content

    def start_game(self):
        network_obj.send_tcp(("s", ""))

    def leave_lobby(self):
        network_obj.disconnect()
        game.change_state(main.TitleState())


class MultiplayerGameState():
    def __init__(self):
        network_obj.send_tcp(("r", None))

        # game settings
        self.max_time = 10
        self.bonus_time = 1

        self.cp = None  # Word player is typing
        self.cp_count = 1  # Count or index of current word

        self.finished = True

        for i, p in enumerate(game.player_list.values()):
            p["remaining_time"] = self.max_time
            p["alive"] = True
            p["ypos"] = i

        # delta time stuff
        self.previous_time = time.time()

        self.word_win = curses.newwin(len(game.player_list), 35, 3, 5)

        self.draw()

        self.fx = screen.FX()

    def draw(self):
        game.stdscr.clear()
        game.stdscr.addstr(0, 0, "Game")

        self.draw_words()
        self.draw_timer()

        curses.doupdate()

    def draw_words(self):
        self.word_win.clear()

        for p in game.player_list.values():
            color = curses.color_pair(1) if p == game.me() else 0

            if p["alive"] and self.cp:
                self.word_win.addstr(
                    p["ypos"], 20 + p["word_index"], self.cp.phrase[p["word_index"]:])
            else:
                color = curses.color_pair(4)

            self.word_win.addstr(p["ypos"], 0, p["name"] + ":", color)

        # underline on current character
        if game.me("alive") and self.cp:
            i = game.me("word_index")
            if game.me("word_index") < len(self.cp.phrase):
                self.word_win.addstr(
                    game.me("ypos"), 20 + i, self.cp.phrase[i], curses.A_UNDERLINE)

        self.word_win.noutrefresh()

    def draw_timer(self):
        for p in game.player_list.values():
            if p["remaining_time"] > 5:
                color = 1
            elif p["remaining_time"] > 2:
                color = 2
            elif p["remaining_time"] > 0:
                color = 3
            else:
                color = 4
            # clear the previous text
            game.stdscr.addstr(3 + p["ypos"], 60, " " * 5)
            game.stdscr.addstr(3 + p["ypos"], 60, f"{p["remaining_time"]:.2f}",
                               curses.color_pair(color))
        game.stdscr.noutrefresh()

    def update(self):
        currentTime = time.time()
        deltaTime = currentTime - self.previous_time
        self.previous_time = currentTime

        key = game.stdscr.getch()
        if self.cp:
            # update timer:
            for p in game.player_list.values():
                if p["word_index"] < len(self.cp.phrase) and p["alive"]:
                    p["remaining_time"] = max(
                        0, p["remaining_time"] - deltaTime)
                    self.draw_timer()

            if not self.finished and game.me("alive"):
                if self.cp.type_char(key):
                    game.me()["word_index"] += 1
                    self.draw_words()

                    curr_i = game.me("word_index")

                    network_obj.send_udp(("i", curr_i))

                    # IF player finishes phrase
                    if curr_i >= len(self.cp.phrase):
                        self.finished = True
                        self.cp.finish()

                        # Add bonus time and update server
                        game.me()["remaining_time"] = min(self.max_time,
                                                          game.me("remaining_time") + self.bonus_time)
                        network_obj.send_tcp(
                            ("r", (game.me("remaining_time"),
                                   self.cp.time_taken())))

                        # Show bonus time text
                        self.fx.add(screen.FXObject_Fade(
                            0.5, 3 + game.me("ypos"), 65, f"(+{self.bonus_time:.2f}s)", game.stdscr))

                # If you run out of time
                if game.me("alive") and game.me("remaining_time") <= 0:
                    game.me()["alive"] = False
                    self.cp.finish()
                    network_obj.send_tcp(("d", ""))

        if not network_obj.recv_queue.empty():

            prefix, content = network_obj.recv_queue.get()

            if prefix == "w":
                self.cp_count, phrase = content
                self.cp = Phrase(phrase)
                if game.me("alive"):
                    game.phrases.append(self.cp)

                self.finished = False

                for player_data in game.player_list.values():
                    player_data["word_index"] = 0

                self.draw_words()

            elif prefix == "i":
                w_index, stuff = content
                if w_index == self.cp_count:
                    for id, char_index in stuff.items():
                        if id != game.my_id:
                            game.player_list[id]["word_index"] = char_index
                self.draw_words()

            elif prefix == "t":
                id, stuff = content
                game.player_list[id]["remaining_time"] = stuff
                self.fx.add(screen.FXObject_Fade(
                    0.5, 3 + game.player_list[id]["ypos"], 65, f"(+{self.bonus_time:.2f}s)", game.stdscr))
                self.draw_timer()

            elif prefix == "d":
                game.player_list[content]["remaining_time"] = 0
                game.player_list[content]["alive"] = False
                self.draw_timer()
            elif prefix == "s":
                game.change_state(screen.PopupState(
                    "Game Ended!", ScoreScreenState))

        self.fx.update()
        curses.doupdate()


class ScoreScreenState():
    def __init__(self):
        game.stdscr.clear()
        game.stdscr.addstr(0, 0, "Score Screen")
        game.stdscr.addstr(1, 0, "Getting results...")
        network_obj.send_tcp(("q", {"wpm": game.get_wpm(),
                                    "acc": game.get_accuracy(),
                                    "avg_r": game.get_avg_reaction(),
                                    "score": game.get_score()}))
        game.stdscr.refresh()
        self.data = None
        self.options = screen.OptionSelect(game.stdscr,
                                           ["Leave game", "Re-join lobby"],
                                           [None,
                                            lambda: game.change_state(LobbyState())],
                                           10, 0)

    def draw(self):
        if not self.data:
            return
        game.stdscr.clear()
        game.stdscr.addstr(0, 0, "Score Screen")
        game.stdscr.addstr(1, 15, "Accuracy:")
        game.stdscr.addstr(1, 30, "Score:")
        game.stdscr.addstr(1, 40, "Speed:")
        game.stdscr.addstr(1, 50, "Avg Reaction Time:")
        for k, v in self.data.items():
            ypos = game.player_list[k]["ypos"] + 2
            name = game.player_list[k]["name"]
            game.stdscr.addstr(ypos, 0, name)
            game.stdscr.addstr(ypos, 15, f"{v["acc"]:.2f}%")
            game.stdscr.addstr(ypos, 30, f"{v["score"]}")
            game.stdscr.addstr(ypos, 40, f"{v["wpm"]:.0f} WPM")
            game.stdscr.addstr(ypos, 50, f"{v["avg_r"]:.4f}s")
        self.options.draw()
        game.stdscr.refresh()

    def update(self):
        self.options.update_loop()
        if not network_obj.recv_queue.empty():
            prefix, content = network_obj.recv_queue.get()
            if prefix == "q":
                self.data = content
                self.draw()
