import socket

# TODO: Complete with a short-read/short-write tolerant implementation


def recv_all(socket: socket.socket, size):
    bytes_recv = 0
    data = b""
    while bytes_recv < size:
        chunk = socket.recv(size - bytes_recv)
        if not chunk:
            raise ConnectionError("Socket connection closed before receiving all data")
        data += chunk
        bytes_recv += len(chunk)
    return data


def send_all(socket: socket.socket, bytes):
    while len(bytes) > 0:
        sent = socket.send(bytes)
        bytes = bytes[sent:]
    return socket.send(bytes)
