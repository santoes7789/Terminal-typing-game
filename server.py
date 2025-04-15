import socket
import selectors
import json
import config
import utils
import time

HOST = ""
PORT = config.PORT


connections = []
next_id = 1
word_index = 0
current_phrase = ""


class Connection:
    def __init__(self, selector, sock, addr, onrecv, id):
        self.selector = selector
        self.sock = sock
        self.addr = addr
        self.onrecv = onrecv
        self.write_buffer = b""
        self.name = ""
        self.id = id

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
    player_list = []
    for conn in connections:
        player_list.append({"id": conn.id, "name": conn.name})
    message = "p" + json.dumps(player_list)
    return message.encode("utf-8")


# message prefixes:
# client request
# lobby:
# p -> client requests for full player list
# m -> client sends message
# n -> client request to set/change name
# s -> client requests to start game

# game:
# i -> client to tell what index of word they are on


# server request
# o -> give client id
# w -> give client word
# f -> notify word has finished
# s -> tell client to start game
# i -> broadcast for index of work

def on_receive_message(sender, prefix, recv):
    global word_index

    def broadcast(message):
        for conn in connections:
            conn.write_buffer += message
            conn.write()

    def send_new_word():
        global current_phrase, word_index
        current_phrase = utils.generate_rand_word(3)
        word_index += 1
        send = ("w" + current_phrase).encode("utf-8")
        broadcast(send)

    if prefix == "p":
        broadcast(format_conns_list())

    elif prefix == "m":
        message = {"id": sender.id, "message": recv}
        send = ("m" + json.dumps(message)).encode("utf-8")
        broadcast(send)

    elif prefix == "n":
        sender.name = recv
        broadcast(format_conns_list())

    elif prefix == "s":
        word_index = 0
        send = "s".encode("utf-8")
        broadcast(send)
        time.sleep(2)
        send_new_word()

    elif prefix == "i":
        message = {"id": sender.id, "index": int(recv)}
        send = ("i" + json.dumps(message)).encode("utf-8")
        broadcast(send)
        if (int(recv) == len(current_phrase)):
            send = ("f" + str(word_index)).encode("utf-8")
            broadcast(send)
            send_new_word()


def accept_new_connection(sock):
    global next_id
    conn, addr = sock.accept()
    conn.setblocking(False)
    print("Accepted connection from ", addr)
    obj = Connection(sel, conn, addr, on_receive_message, next_id)
    connections.append(obj)
    sel.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, data=obj)
    obj.write_buffer += ("o" + str(next_id)).encode("utf-8")
    obj.write()
    next_id += 1


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
