from enum import Enum

class MessageType(Enum):
    ERROR = 0x00
    START = 0x01
    BET = 0x02
    END = 0x03
    ACK = 0x04
    WINNERS = 0x05