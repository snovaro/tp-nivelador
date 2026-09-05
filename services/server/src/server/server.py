import socket
import logger
import safe_socket
from server.server_protocol import ServerProtocol
from lottery.lottery import Lottery

_ECHO_SERVER_MESSAGE_SIZE = 1024


class Server:
    def __init__(self, server_host: str, server_port: int, storage_path: str) -> None:
        self.server_host = server_host
        self.server_port = server_port
        self.storage_path = storage_path
        self.lottery = Lottery(storage_path)

    def _handle_client(self, client_socket):
        action = "handle-client"
        message_amount = 0
        protocol = ServerProtocol(client_socket)
        try:
            logger.info(action, logger.LogResult.in_progress)
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
                if type_message == 0x02:  # BET message type
                    # Process the BET message payload here
                    # For example, you can parse the payload and perform necessary actions
                    bet = protocol.deserialize_bet(payload)
                    self.lottery.set_agency_id(bet.agency_id)
                    self.lottery.store_bets([bet])
                    message_amount += 1
                    #safe_socket.send_all(client_socket, client_message)
        except Exception as e:
            logger.error(
                action, logger.LogResult.fail, "messages-amount", message_amount
            )
            raise e
        finally:
            client_socket.close()

    def run(self):
        action = "accept-connection"
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.server_host, self.server_port))
            server_socket.listen()
            while True:
                try:
                    logger.info(action, logger.LogResult.in_progress)
                    client_socket, _ = server_socket.accept()
                except Exception as e:
                    logger.error(action, logger.LogResult.fail)
                    raise e
                logger.info(action, logger.LogResult.success)

                self._handle_client(client_socket)
