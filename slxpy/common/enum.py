from enum import Enum


class FieldMode(Enum):
    MODEL = 0
    PLAIN = 1
    PLAIN_ARRAY = 2
    STRUCT = 3
    STRUCT_ARRAY = 4
    ENUM = 5
    ENUM_ARRAY = 6
    POINTER = 7
    POINTER_ARRAY = 8
