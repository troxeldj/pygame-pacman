from enum import Enum, auto


class GameState(Enum):
    MAIN_MENU = auto()
    PLAYING = auto()
    GAME_OVER = auto()
    WIN = auto()
    QUIT = auto()
