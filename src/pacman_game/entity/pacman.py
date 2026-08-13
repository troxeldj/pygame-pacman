from pathlib import Path

import pygame

from ..game_map import GameMap
from ..orientation import Orientation
from ..position import Position
from .entity import Entity

_ASSETS_DIR = Path(__file__).parent.parent.parent.parent / "assets"

_IMAGE_PATHS: dict[Orientation, list[Path]] = {
    Orientation.LEFT: [_ASSETS_DIR / "pacman-left" / f"{i}.png" for i in (1, 2, 3)],
    Orientation.RIGHT: [_ASSETS_DIR / "pacman-right" / f"{i}.png" for i in (1, 2, 3)],
    Orientation.UP: [_ASSETS_DIR / "pacman-up" / f"{i}.png" for i in (1, 2, 3)],
    Orientation.DOWN: [_ASSETS_DIR / "pacman-down" / f"{i}.png" for i in (1, 2, 3)],
}


class Pacman(Entity):
    def __init__(
        self,
        position: Position,
        orientation: Orientation = Orientation.RIGHT,
        speed: float = 5.0,
    ) -> None:
        images = {
            facing: [pygame.image.load(path) for path in paths]
            for facing, paths in _IMAGE_PATHS.items()
        }
        super().__init__(
            position=position, orientation=orientation, images=images, speed=speed
        )
        self._requested_orientation: Orientation | None = None

    def change_orientation(self, new_orientation: Orientation) -> None:
        self._requested_orientation = new_orientation

    def _next_orientation(self, game_map: GameMap) -> Orientation:
        if self._requested_orientation is not None:
            dx, dy = self._requested_orientation.delta
            if game_map.is_walkable(self.position.x + dx, self.position.y + dy):
                return self._requested_orientation

        return self.orientation
