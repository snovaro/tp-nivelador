from enum import Enum

class MessageType(Enum):
    START = 0x01
    BET = 0x02
    FIN = 0x03
    ERROR = 0x04