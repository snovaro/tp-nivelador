import signal
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
        self.draw = 1
        self.lottery = Lottery(self.storage_path + f"/draw_{self.draw}.csv")
        self.client_handlers = []
        self.server_state = ServerState(quorum_min)
        self.shutdown_event = threading.Event()

        signal.signal(
            signal.SIGTERM,
            self.handle_sigterm
        )

    def handle_sigterm(self, signum, frame):
        logger.info("shutdown", logger.LogResult.in_progress)
        self.shutdown_event.set()
        self.server_state.shutdown()
        

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.server_host, self.server_port))
            server_socket.listen()
            try:
                self.accepter_loop(server_socket)

            finally:
                for client_handler in self.client_handlers:
                    client_handler.kill()
                    client_handler.join()

    def accepter_loop(self, server_socket: socket.socket):
        server_socket.settimeout(1.0)
        while not self.shutdown_event.is_set():
            try:
                logger.info("accept-connection", logger.LogResult.in_progress)
                client_socket, _ = server_socket.accept()
            except socket.timeout:
                continue
            except Exception as e:
                logger.error("accept-connection", logger.LogResult.fail)
                raise e
            logger.info("accept-connection", logger.LogResult.success)
            self.start_client()
            client_handler = ClientHandler(client_socket, self.lottery, self.server_state)
            client_handler.start()
            self.client_handlers.append(client_handler)

    def start_client(self):
        try:
            self.server_state.client_started()
        except DrawCompleteException as e:
            self.draw += 1
            self.lottery = Lottery(self.storage_path + f"/draw_{self.draw}.csv")
            self.server_state = ServerState(self.server_state.quorum_min)
            self.server_state.client_started()