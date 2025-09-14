from enum import IntEnum


class MessageStatus(IntEnum):
    PENDING = 0
    PROCESSING = 1
    COMPLETED = 2
    FAILED = 3
    RETRYING = 4

