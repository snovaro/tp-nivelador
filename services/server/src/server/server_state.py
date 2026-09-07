import threading

from server.draw_complete_exception import DrawCompleteException


class ServerState:
    def __init__(self, quorum_min: int) -> None:
        self.cv = threading.Condition()
        self.finished_clients = 0
        self.started_clients = 0
        self.quorum_min = quorum_min

    def client_started(self):
        with self.cv:
            if self.is_draw_complete():
                raise DrawCompleteException("Cannot start new client, draw done")
            self.started_clients += 1


    def is_draw_complete(self):
        return self.finished_clients >= self.quorum_min and self.started_clients == 0

    def finished_client(self):
        with self.cv:
            self.finished_clients += 1
            self.started_clients -= 1
            self.cv.notify_all()


    def wait_for_quorum(self):
        with self.cv:
            while not self.is_draw_complete():
                self.cv.wait()

    def shutdown(self):
        with self.cv:
            self.finished_clients = self.quorum_min
            self.started_clients = 0
            self.cv.notify_all()