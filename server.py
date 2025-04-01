import socket
import selectors
import struct
import config
import utils
import time

HOST = ""
PORT = config.PORT


connections = []
current_phrase = ""


class Connection:
    def __init__(self, selector, sock, addr, onrecv):
        self.selector = selector
        self.sock = sock
        self.addr = addr
        self.onrecv = onrecv
        self.write_buffer = b""
        self.name = ""

    def close(self):
        print("Disconnected ", self.addr)
        self.selector.unregister(self.sock)
        self.sock.close()
        connections.remove(self)

    def write(self):
        if self.write_buffer:
            try:
                utils.send_message(self.sock, self.write_buffer)
            except Exception as e:
                print(e)
                self.close()
                return

            print("Sent '" + self.write_buffer.decode(
                "utf-8") + "' to ", self.addr)
            self.write_buffer = b""

    def read(self):
        try:
            prefix, recv_data = utils.parse_message(self.sock)
        except Exception as e:
            print(e)
            self.close()
            return
        print("Recieved from {}: ({}) {}".format(
            self.addr, prefix, recv_data))

        self.onrecv(self, prefix, recv_data)

    def process_events(self, mask):
        if mask & selectors.EVENT_WRITE:
            self.write()

        if mask & selectors.EVENT_READ:
            self.read()


sel = selectors.DefaultSelector()

lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
lsock.bind((HOST, PORT))
lsock.listen()
print("Listening on {}".format((HOST, PORT)))
lsock.setblocking(False)

sel.register(lsock, selectors.EVENT_READ)


def format_conns_list():
    player_list = "p"
    for conn in connections:
        player_list += conn.name + "\n"
    player_list = player_list[:-1]
    return player_list.encode("utf-8")


# message prefixes:
# lobby:
# p -> client requests for full player list
# m -> client sends message
# n -> client request to set/change name
# s -> client requests to start game

# game:
# i -> client to tell what index of word they are on


def on_receive_message(sender, prefix, recv):

    def send_new_word():
        global current_phrase
        current_phrase = utils.generate_rand_word(3)
        message = ("w" + current_phrase).encode("utf-8")
        for conn in connections:
            conn.write_buffer += message
            conn.write()

    if prefix == "p":
        # consider using json dump? maybe not i dont know
        sender.write_buffer += format_conns_list()

    elif prefix == "m":
        message = ("m" + recv).encode("utf-8")
        for conn in connections:
            conn.write_buffer += message

    elif prefix == "n":
        sender.name = recv
        for conn in connections:
            conn.write_buffer += format_conns_list()

    elif prefix == "s":
        message = "s".encode("utf-8")
        for conn in connections:
            conn.write_buffer += message
            conn.write()

        time.sleep(5)
        send_new_word()

    elif prefix == "i":
        if (int(recv) == len(current_phrase)):
            for conn in connections:
                conn.write_buffer += "f".encode("utf-8")
                conn.write()
            send_new_word()


def accept_new_connection(sock):
    conn, addr = sock.accept()
    conn.setblocking(False)
    print("Accepted connection from ", addr)
    obj = Connection(sel, conn, addr, on_receive_message)
    connections.append(obj)
    sel.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, data=obj)


try:
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_new_connection(key.fileobj)
            else:
                key.data.process_events(mask)

except KeyboardInterrupt:
    print("\nCaught keyboard interrupt, exiting")
finally:
    print("Closing socket")
    sel.close()
    lsock.close()
