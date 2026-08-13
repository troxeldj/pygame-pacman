from enum import Enum, auto


class Orientation(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()

    @property
    def delta(self) -> tuple[int, int]:
        return {
            Orientation.UP: (0, -1),
            Orientation.DOWN: (0, 1),
            Orientation.LEFT: (-1, 0),
            Orientation.RIGHT: (1, 0),
        }[self]

    @property
    def opposite(self) -> "Orientation":
        return {
            Orientation.UP: Orientation.DOWN,
            Orientation.DOWN: Orientation.UP,
            Orientation.LEFT: Orientation.RIGHT,
            Orientation.RIGHT: Orientation.LEFT,
        }[self]
