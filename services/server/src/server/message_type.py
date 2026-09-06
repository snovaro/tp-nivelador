from enum import Enum

class MessageType(Enum):
    BET = 0x01
    END = 0x02
    ACK = 0x03
    WINNERS = 0x04
    BATCH = 0x05