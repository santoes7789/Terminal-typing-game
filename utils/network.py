import pickle


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
