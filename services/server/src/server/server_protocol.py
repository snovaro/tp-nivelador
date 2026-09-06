from lottery.bet import Bet
from safe_socket.safe_socket import recv_all, send_all
from server.message_type import MessageType

class ServerProtocol:
    def __init__(self, client_socket) -> None:
        self.client_socket = client_socket

    def send(self, message: bytes) -> None:
        send_all(self.client_socket, message)

    def receive(self, size: int) -> bytes:
        return recv_all(self.client_socket, size)

    def receive_header(self) -> tuple[MessageType, int]:
        header = self.receive(3)
        type_message = MessageType(header[0])
        length = int.from_bytes(header[1:3], byteorder="big")
        return type_message, length

    def receive_payload(self, length: int) -> bytes:
        return self.receive(length)

    def receive_message(self) -> tuple[MessageType, bytes]:
        type_message, length = self.receive_header()
        payload = self.receive_payload(length)
        return type_message, payload

    def deserialize_bet(self, payload: bytes) -> Bet:
        try:
            pos = 0
            agency_id = payload[pos]
            pos += 1
            name, pos = self.deserialize_string(payload, pos)
            surname, pos = self.deserialize_string(payload, pos)
            dni = int.from_bytes(payload[pos : pos + 4], byteorder="big")
            pos += 4
            year = int.from_bytes(payload[pos : pos + 2], byteorder="big")
            pos += 2
            month = payload[pos]
            pos += 1
            day = payload[pos]
            pos += 1
            bet_number = int.from_bytes(payload[pos : pos + 2], byteorder="big")
            pos += 2
        except IndexError:
            raise ValueError("Payload is too short to deserialize Bet")
        except TimeoutError:
            raise TimeoutError("Socket operation timed out while deserializing Bet")
        except Exception as e:
            raise ValueError(f"Error while deserializing Bet: {e}")
        if pos != len(payload):
            raise ValueError("Payload length does not match expected length")
        birthdate = f"{year:04d}-{month:02d}-{day:02d}"
        return Bet(agency_id, name, surname, dni, birthdate, bet_number)

    def deserialize_string(self, payload: bytes, pos: int) -> tuple[str, int]:
        length = payload[pos]
        pos += 1
        string_value = payload[pos : pos + length].decode("utf-8")
        pos += length
        return string_value, pos

    def send_ack(self) -> None:
        header = bytes([MessageType.ACK.value]) + (0).to_bytes(2, byteorder="big")
        self.send(header)


    def send_winners(self, winners: list[Bet]) -> None:
        payload = b""
        for winner in winners:
            payload += self.serialize_bet(winner)
        type_message = MessageType.WINNERS
        length = len(payload)
        header = bytes([type_message.value]) + length.to_bytes(2, byteorder="big")
        self.send(header + payload)


    def serialize_bet(self, bet: Bet) -> bytes:
        agency_id_bytes = bytes([bet.agency_id])
        name_bytes = bet.first_name.encode("utf-8")
        surname_bytes = bet.last_name.encode("utf-8")
        dni_bytes = bet.document.to_bytes(4, byteorder="big")
        year, month, day = map(int, bet.birthdate.split("-"))
        year_bytes = year.to_bytes(2, byteorder="big")
        month_byte = bytes([month])
        day_byte = bytes([day])
        bet_number_bytes = bet.number.to_bytes(2, byteorder="big")

        payload = (
            bytes(agency_id_bytes) +
            bytes([len(name_bytes)]) + name_bytes +
            bytes([len(surname_bytes)]) + surname_bytes +
            dni_bytes +
            year_bytes + month_byte + day_byte +
            bet_number_bytes
        )
        return payload