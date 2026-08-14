import random
from pathlib import Path

import pygame

from ..game_map import GameMap, MapLayout
from ..orientation import Orientation
from ..pathing import bfs_next_step
from ..position import Position
from .entity import Entity
from .pacman import Pacman

_ASSETS_DIR = Path(__file__).parent.parent.parent.parent / "assets" / "ghosts"

_IMAGE_PATHS: dict[str, Path] = {
    "blinky": _ASSETS_DIR / "blinky.png",
    "pinky": _ASSETS_DIR / "pinky.png",
    "inky": _ASSETS_DIR / "inky.png",
    "clyde": _ASSETS_DIR / "clyde.png",
}
_FRIGHTENED_IMAGE_PATH = _ASSETS_DIR / "blue_ghost.png"

_PINKY_AMBUSH_DISTANCE = 4
_INKY_FLANK_DISTANCE = 2
_CLYDE_CHASE_RADIUS_SQ = 64


def _squared_distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(value, high))


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
        self._pending_respawn = False
        self.respawn_timer = 0.0
        self._spawn = (position.x, position.y)
        self._target = self._spawn
        self._pacman_position = self._spawn
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

    @property
    def pending_respawn(self) -> bool:
        return self._pending_respawn

    def start_respawn_delay(self, duration: float) -> None:
        self._pending_respawn = True
        self.respawn_timer = duration

    def clear_respawn_delay(self) -> None:
        self._pending_respawn = False
        self.respawn_timer = 0.0

    def update(self, dt: float, game_map: GameMap) -> None:
        if self._pending_respawn:
            return
        super().update(dt, game_map)

    def draw(self, surface: pygame.Surface, layout: MapLayout) -> None:
        if self._pending_respawn:
            return
        super().draw(surface, layout)

    def update_target(self, pacman: Pacman, game_map: GameMap) -> None:
        if self._pending_respawn:
            return
        pacman_pos = (pacman.position.x, pacman.position.y)
        self._pacman_position = pacman_pos
        self._target = self._compute_target(pacman, pacman_pos, game_map)

    def _compute_target(
        self,
        pacman: Pacman,
        pacman_pos: tuple[int, int],
        game_map: GameMap,
    ) -> tuple[int, int]:
        dx, dy = pacman.orientation.delta

        if self.color == "pinky":
            return (
                _clamp(pacman_pos[0] + dx * _PINKY_AMBUSH_DISTANCE, 0, game_map.width - 1),
                _clamp(pacman_pos[1] + dy * _PINKY_AMBUSH_DISTANCE, 0, game_map.height - 1),
            )

        if self.color == "inky":
            ahead_x = pacman_pos[0] + dx * _INKY_FLANK_DISTANCE
            ahead_y = pacman_pos[1] + dy * _INKY_FLANK_DISTANCE
            return (
                _clamp(ahead_x + dy * _INKY_FLANK_DISTANCE, 0, game_map.width - 1),
                _clamp(ahead_y + dx * _INKY_FLANK_DISTANCE, 0, game_map.height - 1),
            )

        if self.color == "clyde":
            if _squared_distance(
                (self.position.x, self.position.y), pacman_pos
            ) > _CLYDE_CHASE_RADIUS_SQ:
                return pacman_pos
            return self._spawn

        return pacman_pos

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
        non_reverse = non_reverse or walkable

        if self._frightened:
            return max(
                non_reverse,
                key=lambda o: _squared_distance(
                    (
                        self.position.x + o.delta[0],
                        self.position.y + o.delta[1],
                    ),
                    self._pacman_position,
                ),
            )

        next_step = bfs_next_step(
            (self.position.x, self.position.y), self._target, game_map
        )
        if next_step is not None:
            return next_step

        return random.choice(non_reverse)
