import socket

TIMEOUT = 5  # Set a timeout of 5 seconds

def recv_all(socket: socket.socket, size):
    bytes_recv = 0
    data = b""
    socket.settimeout(TIMEOUT)
    while bytes_recv < size:
        try:
            chunk = socket.recv(size - bytes_recv)
        except socket.timeout:
            raise TimeoutError("Socket operation timed out")
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
