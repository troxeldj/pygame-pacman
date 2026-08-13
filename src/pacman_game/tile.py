from enum import Enum, auto


class Tile(Enum):
    EMPTY = auto()
    WALL = auto()
    DOT = auto()
    POWER_PELLET = auto()
