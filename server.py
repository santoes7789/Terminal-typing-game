import socket
import selectors
import struct
import config
import utils

HOST = "127.0.0.1"
PORT = config.PORT


connections = []


class Connection:
    def __init__(self, selector, sock, addr, onrecv):
        self.selector = selector
        self.sock = sock
        self.addr = addr
        self.onrecv = onrecv
        self.read_buffer = b""
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
            recv_data = utils.parse_message(self.sock)
        except Exception as e:
            print(e)
            self.close()
            return

        self.read_buffer = recv_data
        print("Recieved from {}: {}".format(
            self.addr, recv_data.decode("utf-8")))

        if self.name:
            self.onrecv(self)
        else:
            self.name = self.read_buffer

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


# message prefixes:
# p -> client requests for full player list
# m -> client sends message
def on_receive_message(sender):
    recv = sender.read_buffer.decode("utf-8")
    prefix = recv[0]
    recv = recv[1:]
    if prefix == "p":
        pass
    elif prefix == "m":
        message = recv.encode("utf-8")
        for conn in connections:
            conn.write_buffer += message


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
