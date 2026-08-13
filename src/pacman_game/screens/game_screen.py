from pathlib import Path

import pygame

from ..entity.entity import Entity
from ..entity.ghost import Ghost
from ..entity.pacman import Pacman
from ..game_map import GameMap
from ..game_state import GameState
from ..orientation import Orientation
from ..position import Position
from .screen import Screen

_GHOST_COLORS = ["blinky", "pinky", "inky", "clyde"]
_STARTING_LIVES = 3
_DOT_SCORE = 10


class GameScreen(Screen):
    def __init__(self) -> None:
        levels_dir = Path(__file__).parent.parent.parent.parent / "assets" / "levels"
        self._levels: list[Path] = sorted(levels_dir.glob("*.txt"))
        self._lives = _STARTING_LIVES
        self.score = 0
        self._hud_font = pygame.font.SysFont(None, 28)

        self._load_level(0)

    def _load_level(self, index: int) -> None:
        self._level_index = index
        self._game_map: GameMap = GameMap.load(self._levels[index])
        self._reset_entities()

    def _reset_entities(self) -> None:
        pacman_x, pacman_y = self._game_map.pacman_start
        self._pacman = Pacman(
            position=Position(x=pacman_x, y=pacman_y),
            orientation=Orientation.RIGHT,
        )
        self._ghosts = [
            Ghost(
                position=Position(x=x, y=y),
                color=_GHOST_COLORS[i % len(_GHOST_COLORS)],
            )
            for i, (x, y) in enumerate(self._game_map.ghost_spawns)
        ]
        self._entities: list[Entity] = [self._pacman, *self._ghosts]

    def handle_event(self, event: pygame.event.Event) -> GameState | None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return GameState.MAIN_MENU
            elif event.key == pygame.K_UP:
                self._pacman.change_orientation(Orientation.UP)
            elif event.key == pygame.K_DOWN:
                self._pacman.change_orientation(Orientation.DOWN)
            elif event.key == pygame.K_LEFT:
                self._pacman.change_orientation(Orientation.LEFT)
            elif event.key == pygame.K_RIGHT:
                self._pacman.change_orientation(Orientation.RIGHT)
        return None

    def update(self, dt: float) -> GameState | None:
        for entity in self._entities:
            entity.update(dt, self._game_map)

        if self._game_map.eat_dot(self._pacman.position.x, self._pacman.position.y):
            self.score += _DOT_SCORE

        for ghost in self._ghosts:
            if (ghost.position.x, ghost.position.y) == (
                self._pacman.position.x,
                self._pacman.position.y,
            ):
                self._lives -= 1
                if self._lives <= 0:
                    return GameState.GAME_OVER
                self._reset_entities()
                break

        if self._game_map.remaining_dots == 0:
            if self._level_index + 1 < len(self._levels):
                self._load_level(self._level_index + 1)
            else:
                return GameState.WIN

        return None

    def draw(self, surface: pygame.Surface) -> None:
        layout = self._game_map.get_layout(surface)

        self._game_map.draw(surface, layout)
        for entity in self._entities:
            entity.draw(surface, layout)

        self._draw_hud(surface)

    def _draw_hud(self, surface: pygame.Surface) -> None:
        lines = [
            f"Lives: {self._lives}",
            f"Level: {self._level_index + 1}",
            f"Score: {self.score}",
        ]
        y = 10
        for line in lines:
            text = self._hud_font.render(line, True, (255, 255, 255))
            surface.blit(text, (10, y))
            y += text.get_height() + 4
