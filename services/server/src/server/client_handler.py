import socket
import logger
from server.server_protocol import ServerProtocol
from lottery.lottery import Lottery
from server.message_type import MessageType


class ClientHandler:
    def __init__(self, client_socket: socket.socket, lottery: Lottery) -> None:
        self.client_socket = client_socket
        self.lottery = lottery


    def _handle_client(self, client_socket):
        action = "handle-client"
        message_amount = 0
        protocol = ServerProtocol(client_socket)
        try:
            logger.info(action, logger.LogResult.in_progress, "Receiving messages from client")
            while True:
                try:
                    type_message, payload = protocol.receive_message()
                except Exception as error:
                    if type(error).__name__ == "ConnectionError":
                        logger.info(
                            action,
                            logger.LogResult.success,
                            "messages-amount",
                            message_amount,
                        )
                        return
                    raise error
                logger.info(
                    action,
                    logger.LogResult.success,
                    "message received",
                    "message-type",
                    type_message,
                )
                match type_message:
                    case MessageType.START:
                        logger.info(
                            action,
                            logger.LogResult.success,
                            "entro en START",
                        )
                    case MessageType.BET:
                        logger.info(
                            "deserializing bet",
                            logger.LogResult.in_progress,
                        )
                        bet = protocol.deserialize_bet(payload)
                        logger.info(
                            "bet deserialized",
                            logger.LogResult.success,
                        )
                        self.lottery.set_agency_id(bet.agency_id)
                        self.lottery.store_bets([bet])
                        logger.info(
                            "bet stored",
                            logger.LogResult.success,
                        )
                        message_amount += 1
                        protocol.send_ack()
                    case MessageType.END:
                        logger.info(
                            "end message received",
                            logger.LogResult.success,
                            "messages-amount",
                            message_amount,
                        )
                        return
                    case MessageType.ERROR:
                        logger.error(
                            "error message received",
                            logger.LogResult.fail,
                        )
        except Exception as e:
            logger.error(
                action, logger.LogResult.fail, "messages-amount", message_amount
            )
            raise e
        finally:
            client_socket.close()


    def run(self):
        self._handle_client(self.client_socket)