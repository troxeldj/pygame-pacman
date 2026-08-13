from dataclasses import dataclass, field

import pygame

from ..game_map import GameMap, MapLayout
from ..orientation import Orientation
from ..position import Position


@dataclass
class Entity:
    position: Position
    orientation: Orientation
    images: dict[Orientation, list[pygame.Surface]]
    speed: float = 4.0

    _scaled_images: dict[Orientation, list[pygame.Surface]] = field(
        init=False, repr=False, compare=False
    )
    _scaled_tile_size: int | None = field(
        default=None, init=False, repr=False, compare=False
    )
    _progress: float = field(default=0.0, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        self._scaled_images = dict(self.images)
        self._scaled_tile_size = None

    def change_orientation(self, new_orientation: Orientation) -> None:
        self.orientation = new_orientation

    def move(self, velocity: int) -> None:
        dx, dy = self.orientation.delta
        self.position.x += dx * velocity
        self.position.y += dy * velocity

    def update(self, dt: float, game_map: GameMap) -> None:
        dx, dy = self.orientation.delta
        if not game_map.is_walkable(self.position.x + dx, self.position.y + dy):
            # Blocked: re-poll every frame (not just at tile boundaries) so a
            # freshly requested direction can take over as soon as it's
            # walkable, instead of leaving the entity stuck facing the wall.
            self.orientation = self._next_orientation(game_map)
            self._progress = 0.0
            return

        self._progress += dt * self.speed
        while self._progress >= 1.0:
            self._progress -= 1.0
            self.move(1)
            self.orientation = self._next_orientation(game_map)
            dx, dy = self.orientation.delta
            if not game_map.is_walkable(self.position.x + dx, self.position.y + dy):
                self._progress = 0.0
                break

    def _next_orientation(self, game_map: GameMap) -> Orientation:
        return self.orientation

    def _ensure_scaled(self, tile_size: int) -> None:
        if self._scaled_tile_size == tile_size:
            return

        self._scaled_images = {
            orientation: [
                pygame.transform.scale(frame, (tile_size, tile_size))
                for frame in frames
            ]
            for orientation, frames in self.images.items()
        }
        self._scaled_tile_size = tile_size

    def draw(self, surface: pygame.Surface, layout: MapLayout) -> None:
        self._ensure_scaled(layout.tile_size)

        dx, dy = self.orientation.delta
        render_x = self.position.x + dx * self._progress
        render_y = self.position.y + dy * self._progress

        x, y = layout.to_pixel(render_x, render_y)
        frames = self._scaled_images[self.orientation]
        frame_index = int(self._progress * len(frames)) % len(frames)
        surface.blit(frames[frame_index], (x, y))
