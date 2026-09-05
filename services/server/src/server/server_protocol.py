class ServerProtocol:
    def __init__(self, client_socket) -> None:
        self.client_socket = client_socket

    def send(self, message: bytes) -> None:
        self.client_socket.send_all(self.client_socket, message)

    def receive(self, size: int) -> bytes:
        return self.client_socket.recv_all(self.client_socket, size)

"""
Byte order: Big Endian
Strings: UTF-8

MESSAGE HEADER
    type:   1 byte
    length: 2 bytes 
    (MAX 522 bytes de payload suponiendo que no coloque limitantes y acepte el largo maximo de 255 bytes de nombre y 255 bytes de apellido)

MESSAGE TYPES
    0x01 START
    0x02 BET
    0x03 FIN
    0x04 ERROR

BET PAYLOAD
    name_length:      uint8
    name:             N bytes
    surname_length:   uint8
    surname:          M bytes
    dni:              uint32
    year:             uint16
    month:            uint8
    day:              uint8
    bet_number:       uint16
"""