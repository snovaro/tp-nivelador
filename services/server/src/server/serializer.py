from lottery.bet import Bet
from safe_socket.safe_socket import recv_all, send_all
from server.message_type import MessageType

class Serializer:

    def deserialize_bet(self, payload: bytes) -> Bet:
        bet, pos = self._deserialize_bet(payload)
        self._check_payload_length(payload, pos)
        return bet

    def _check_payload_length(self, payload: bytes, pos: int):
        if pos != len(payload):
            raise ValueError("Payload length does not match expected length")

    def _deserialize_bet(self, payload: bytes) -> Bet:
        try:
            pos = 0
            agency_id = payload[pos]
            pos += 1
            name, pos = self._deserialize_string(payload, pos)
            surname, pos = self._deserialize_string(payload, pos)
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
        except Exception as e:
            raise ValueError(f"Error while deserializing Bet: {e}")
        birthdate = f"{year:04d}-{month:02d}-{day:02d}"
        return Bet(agency_id, name, surname, dni, birthdate, bet_number), pos
    

    def _deserialize_string(self, payload: bytes, pos: int) -> tuple[str, int]:
        length = payload[pos]
        pos += 1
        string_value = payload[pos : pos + length].decode("utf-8")
        pos += length
        return string_value, pos

    def serialize_winners(self, winners: list[Bet]) -> bytes:
        payload = b""
        for winner in winners:
            payload += self._serialize_bet(winner)
        return payload

    def _serialize_bet(self, bet: Bet) -> bytes:
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


    def deserialize_batch(self, payload: bytes) -> list[Bet]:
        bets = []
        pos = 0
        while pos < len(payload):
            try:
                bet, new_pos = self._deserialize_bet_from_batch(payload, pos)
                bets.append(bet)
                pos = new_pos
            except ValueError as e:
                raise ValueError(f"Error while deserializing batch: {e}")
        self._check_payload_length(payload, pos)
        return bets
