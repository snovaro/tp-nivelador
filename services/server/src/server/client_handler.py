import socket
import threading
import logger
from server.server_protocol import ServerProtocol
from lottery.lottery import Lottery
from server.message_type import MessageType
from server.serializer import Serializer
from server.server_state import ServerState

class ClientHandler(threading.Thread):
    def __init__(self, client_socket: socket.socket, lottery: Lottery, server_state: ServerState) -> None:
        super().__init__()
        self.client_socket = client_socket
        self.lottery = lottery
        self.is_alive = True
        self.serializer = Serializer()
        self.server_state = server_state


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

    def handle_end(self, protocol: ServerProtocol, payload: bytes):
        logger.info(
            "end message received",
            logger.LogResult.success,
        )
        agency_id = payload[0]
        self.server_state.finished_client()
        self.server_state.wait_for_quorum()
        bets = list(self.lottery.load_bets())
        winners = [bet for bet in bets if self.lottery.has_won(bet) and bet.agency_id == agency_id]
        protocol.send_winners(self.serializer.serialize_winners(winners))

        self.kill()

    def handle_error(self):
        logger.error(
            "error message received",
            logger.LogResult.fail,
        )
        self.kill()

    def handle_unknown_message_type(self, type_message):
        logger.error(
            "unknown message type",
            logger.LogResult.fail,
            "message-type",
            type_message,
        )
        self.kill()
    
    def _handle_client(self, client_socket):
        action = "handle-client"
        protocol = ServerProtocol(client_socket)
        try:
            logger.info(action, logger.LogResult.in_progress, "Receiving messages from client")
            while self.is_alive:
                self.handle_message(protocol)
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
                action, logger.LogResult.fail, "unexpected-error", e
            )
            raise e
        finally:
            client_socket.close()

    def handle_message(self, protocol: ServerProtocol):
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
            case MessageType.BATCH:
                self.handle_batch(protocol, payload)
            case MessageType.END:
                self.handle_end(protocol, payload)
            case MessageType.ERROR:
                self.handle_error()
            case _:
                self.handle_unknown_message_type(type_message)

    def run(self):
        self._handle_client(self.client_socket)

    def kill(self):
        self.is_alive = False
        try:
            self.client_socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.client_socket.close()