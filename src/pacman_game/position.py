from dataclasses import dataclass


@dataclass
class Position:
    x: int
    y: int

    def __init__(
        self,
        tuple: tuple[int, int] | None = None,
        x: int | None = None,
        y: int | None = None,
    ):
        if tuple is not None:
            self.x, self.y = tuple
        elif x is not None and y is not None:
            self.x = x
            self.y = y
        else:
            raise ValueError("Either a tuple or both x and y must be provided.")
