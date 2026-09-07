import socket
import logger
from server.server_protocol import ServerProtocol
from lottery.lottery import Lottery
from server.message_type import MessageType
from server.serializer import Serializer


class ClientHandler:
    def __init__(self, client_socket: socket.socket, lottery: Lottery) -> None:
        self.client_socket = client_socket
        self.lottery = lottery
        self.is_alive = True
        self.serializer = Serializer()



    def handle_batch(self, protocol: ServerProtocol, payload: bytes):
        logger.info(
            "deserializing batch",
            logger.LogResult.in_progress,
        )
        bets = self.serializer.deserialize_batch(payload)
        self.lottery.store_bets(bets)
        logger.info(
            "bets stored",
            logger.LogResult.success,
        )
        protocol.send_ack()

    def handle_bet(self, protocol: ServerProtocol, payload: bytes):
        logger.info(
            "deserializing bet",
            logger.LogResult.in_progress,
        )
        bet = self.serializer.deserialize_bet(payload)
        logger.info(
            "bet deserialized",
            logger.LogResult.success,
        )
        self.lottery.store_bets([bet])
        logger.info(
            "bet stored",
            logger.LogResult.success,
        )
        
        protocol.send_ack()

    def handle_end(self, protocol: ServerProtocol, payload: bytes, message_amount: int):
        logger.info(
            "end message received",
            logger.LogResult.success,
            "messages-amount",
            message_amount,
        )
        agency_id = payload[0]
        bets = list(self.lottery.load_bets())
        winners = [bet for bet in bets if self.lottery.has_won(bet) and bet.agency_id == agency_id]
        protocol.send_winners(self.serializer.serialize_winners(winners))

        self._kill()

    def handle_error(self):
        logger.error(
            "error message received",
            logger.LogResult.fail,
        )
        self._kill()

    def handle_unknown_message_type(self, type_message):
        logger.error(
            "unknown message type",
            logger.LogResult.fail,
            "message-type",
            type_message,
        )
        self._kill()
    
    def _handle_client(self, client_socket):
        action = "handle-client"
        message_amount = 0
        protocol = ServerProtocol(client_socket)
        try:
            logger.info(action, logger.LogResult.in_progress, "Receiving messages from client")
            while self.is_alive:
                self.handle_message(protocol, message_amount)
        except ConnectionError as e:
            logger.error(
                    action,
                    logger.LogResult.fail,
                    "connection-error",
                    e
                )
            return
        except Exception as e:
            logger.error(
                action, logger.LogResult.fail, "messages-amount", message_amount
            )
            raise e
        finally:
            client_socket.close()

    def handle_message(self, protocol: ServerProtocol, message_amount: int):
        action = "handle-message"
        type_message, payload = protocol.receive_message()
        logger.info(
            action,
            logger.LogResult.success,
            "message received",
            "message-type",
            type_message,
        )
        match type_message:
            case MessageType.BET:
                self.handle_bet(protocol, payload)
                message_amount += 1
            case MessageType.BATCH:
                self.handle_batch(protocol, payload)
                message_amount += 1
            case MessageType.END:
                self.handle_end(protocol, payload, message_amount)
            case MessageType.ERROR:
                self.handle_error()
            case _:
                self.handle_unknown_message_type(type_message)

    def run(self):
        self._handle_client(self.client_socket)

    def _kill(self):
        self.is_alive = False