from lottery.bet import Bet
from safe_socket.safe_socket import recv_all, send_all
from server.message_type import MessageType

class ServerProtocol:
    def __init__(self, client_socket) -> None:
        self.client_socket = client_socket

    def _send(self, message: bytes) -> None:
        send_all(self.client_socket, message)

    def _receive(self, size: int) -> bytes:
        return recv_all(self.client_socket, size)

    def receive_header(self) -> tuple[MessageType, int]:
        header = self._receive(3)
        type_message = MessageType(header[0])
        length = int.from_bytes(header[1:3], byteorder="big")
        return type_message, length

    def receive_payload(self, length: int) -> bytes:
        return self._receive(length)

    def receive_message(self) -> tuple[MessageType, bytes]:
        type_message, length = self.receive_header()
        payload = self.receive_payload(length)
        return type_message, payload


    def send_ack(self) -> None:
        header = bytes([MessageType.ACK.value]) + (0).to_bytes(2, byteorder="big")
        self._send(header)


    def send_winners(self, payload: bytes) -> None:
        type_message = MessageType.WINNERS
        length = len(payload)
        header = bytes([type_message.value]) + length.to_bytes(2, byteorder="big")
        self._send(header + payload)
