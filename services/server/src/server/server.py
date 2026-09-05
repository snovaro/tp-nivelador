import socket
import logger
from server.server_protocol import ServerProtocol
from lottery.lottery import Lottery
from server.message_type import MessageType
import threading

from server.client_handler import ClientHandler



class Server:
    def __init__(self, server_host: str, server_port: int, storage_path: str) -> None:
        self.server_host = server_host
        self.server_port = server_port
        self.storage_path = storage_path
        self.client_handlers = []

    

    def run(self):
        action = "accept-connection"
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.server_host, self.server_port))
            server_socket.listen()
            try:
                while True:
                    try:
                        logger.info(action, logger.LogResult.in_progress)
                        client_socket, _ = server_socket.accept()
                    except Exception as e:
                        logger.error(action, logger.LogResult.fail)
                        raise e
                    logger.info(action, logger.LogResult.success)

                    client_handler = ClientHandler(client_socket, Lottery(self.storage_path))
                    client_thread = threading.Thread(target=client_handler.run)
                    client_thread.start()
                    self.client_handlers.append(client_thread)
            finally:
                for client_thread in self.client_handlers:
                    client_thread.join()
