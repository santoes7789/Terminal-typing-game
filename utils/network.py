import pickle
import socket
import threading
from queue import Queue

from config import TCP_PORT, UDP_PORT

from utils import helpers


class Network():
    def initialize(self, ip):
        self.ip = ip

        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.settimeout(5.0)
        self.tcp_sock.connect((ip, TCP_PORT))

        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.connect((ip, 0))  # connect where to get lan ip

        self.recv_queue = Queue()

        self.tcp_thread = threading.Thread(
            target=self.tcp_recv_thread, daemon=True)
        self.tcp_thread.start()

        self.udp_thread = threading.Thread(
            target=self.udp_recv_thread, daemon=True)
        self.udp_thread.start()

    def tcp_recv_thread(self):
        self.tcp_sock.settimeout(None)
        try:
            while True:
                message = receive_tcp(self.tcp_sock)
                helpers.debug("(tcp) received :" + str(message))
                self.recv_queue.put(message)
        except Exception as e:
            helpers.debug("Error:" + str(e))
            helpers.debug("Tcp thread stopping")

    def udp_recv_thread(self):
        try:
            while True:
                message, addr = receive_udp(self.udp_sock)
                helpers.debug("(udp) received :" + str(message))
                self.recv_queue.put(message)
        except Exception as e:
            helpers.debug("Error:" + str(e))
            helpers.debug("Udp thread stopping")

    def send_tcp(self, message):
        send_tcp(self.tcp_sock, message)

    def send_udp(self, message):
        send_udp(self.udp_sock, message, (self.ip, UDP_PORT))

    def disconnect(self):
        self.tcp_sock.shutdown(socket.SHUT_RDWR)
        self.tcp_sock.close()

        self.udp_sock.shutdown(socket.SHUT_RDWR)
        self.udp_sock.close()

        self.udp_thread.join()
        self.tcp_thread.join()


def send_tcp(lsock, message):
    message = pickle.dumps(message)

    msg_length = len(message)

    lsock.sendall(msg_length.to_bytes(4, "big") + message)


def receive_tcp(lsock):
    msg_length = lsock.recv(4)

    if not msg_length:
        raise ConnectionResetError

    bytes_to_read = int.from_bytes(msg_length, "big")

    recv_data = lsock.recv(bytes_to_read)

    if not recv_data:
        raise ConnectionResetError

    recv_data = pickle.loads(recv_data)
    return recv_data


def send_udp(lsock, message, addr):
    message = pickle.dumps(message)

    lsock.sendto(message, addr)


def receive_udp(lsock):
    data, addr = lsock.recvfrom(1024)
    data = pickle.loads(data)
    return data, addr
