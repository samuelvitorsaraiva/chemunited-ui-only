from enum import StrEnum


class ProtocolBlock(StrEnum):
    SCRIPT = "script"
    START = "start"
    END = "end"
    LOOP = "loop"
    IF = "if"

