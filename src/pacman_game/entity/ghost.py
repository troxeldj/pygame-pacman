import random
from pathlib import Path

import pygame

from ..game_map import GameMap
from ..orientation import Orientation
from ..position import Position
from .entity import Entity

_ASSETS_DIR = Path(__file__).parent.parent.parent.parent / "assets" / "ghosts"

_IMAGE_PATHS: dict[str, Path] = {
    "blinky": _ASSETS_DIR / "blinky.png",
    "pinky": _ASSETS_DIR / "pinky.png",
    "inky": _ASSETS_DIR / "inky.png",
    "clyde": _ASSETS_DIR / "clyde.png",
}
_FRIGHTENED_IMAGE_PATH = _ASSETS_DIR / "blue_ghost.png"


class Ghost(Entity):
    def __init__(
        self,
        position: Position,
        color: str = "blinky",
        speed: float = 3.5,
    ) -> None:
        self.color = color
        image = pygame.image.load(_IMAGE_PATHS[color])
        frightened_image = pygame.image.load(_FRIGHTENED_IMAGE_PATH)
        self._normal_images = {orientation: [image] for orientation in Orientation}
        self._frightened_images = {
            orientation: [frightened_image] for orientation in Orientation
        }
        self._frightened = False
        super().__init__(
            position=position,
            orientation=Orientation.LEFT,
            images=self._normal_images,
            speed=speed,
        )

    @property
    def frightened(self) -> bool:
        return self._frightened

    def set_frightened(self, active: bool) -> None:
        self._frightened = active
        self.images = self._frightened_images if active else self._normal_images
        self._scaled_tile_size = None

    def _next_orientation(self, game_map: GameMap) -> Orientation:
        walkable = [
            o
            for o in Orientation
            if game_map.is_walkable(
                self.position.x + o.delta[0], self.position.y + o.delta[1]
            )
        ]
        if not walkable:
            return self.orientation

        non_reverse = [o for o in walkable if o != self.orientation.opposite]
        return random.choice(non_reverse or walkable)
