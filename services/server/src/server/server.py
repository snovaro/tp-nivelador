import socket
import logger
from lottery.lottery import Lottery
import threading

from server.client_handler import ClientHandler
from server.draw_complete_exception import DrawCompleteException
from server.server_state import ServerState



class Server:
    def __init__(self, server_host: str, server_port: int, storage_path: str, quorum_min: int) -> None:
        self.server_host = server_host
        self.server_port = server_port
        self.storage_path = storage_path
        self.client_handlers = []
        self.server_state = ServerState(quorum_min)


    def run(self):
        action = "accept-connection"
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.server_host, self.server_port))
            server_socket.listen()
            try:
                while True:
                    self.accepter_loop(server_socket)

            finally:
                for client_thread in self.client_handlers:
                    client_thread.join()

    def accepter_loop(self, server_socket: socket.socket):
        while True:
            try:
                logger.info("accept-connection", logger.LogResult.in_progress)
                client_socket, _ = server_socket.accept()
            except Exception as e:
                logger.error("accept-connection", logger.LogResult.fail)
                raise e
            logger.info("accept-connection", logger.LogResult.success)
            self.start_client()
            client_handler = ClientHandler(client_socket, Lottery(self.storage_path), self.server_state)
            client_thread = threading.Thread(target=client_handler.run)
            client_thread.start()
            self.client_handlers.append(client_thread)

    def start_client(self):
        try:
            self.server_state.client_started()
        except DrawCompleteException as e:
            self.server_state = ServerState(self.server_state.quorum_min)
            self.server_state.client_started()