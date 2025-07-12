def debug(message):
    with open("debug.log", "a") as f:
        f.write(message + "\n")
