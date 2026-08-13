from dataclasses import dataclass
from pathlib import Path

import pygame

from .tile import Tile


@dataclass(frozen=True)
class MapLayout:
    tile_size: int
    offset_x: int
    offset_y: int

    def to_pixel(self, grid_x: float, grid_y: float) -> tuple[int, int]:
        return (
            round(self.offset_x + grid_x * self.tile_size),
            round(self.offset_y + grid_y * self.tile_size),
        )


@dataclass
class GameMap:
    tiles: list[list[Tile]]
    pacman_start: tuple[int, int]
    ghost_spawns: list[tuple[int, int]]

    @property
    def width(self) -> int:
        return len(self.tiles[0])

    @property
    def height(self) -> int:
        return len(self.tiles)

    @classmethod
    def load(cls, path: Path) -> "GameMap":
        lines = path.read_text().splitlines()

        if not lines:
            raise ValueError("Map is empty")

        width = len(lines[0])

        if any(len(line) != width for line in lines):
            raise ValueError("Every map row must have the same width")

        tiles: list[list[Tile]] = []
        pacman_start: tuple[int, int] | None = None
        ghost_spawns: list[tuple[int, int]] = []

        for y, line in enumerate(lines):
            row: list[Tile] = []

            for x, char in enumerate(line):
                match char:
                    case "#":
                        row.append(Tile.WALL)

                    case ".":
                        row.append(Tile.DOT)

                    case "O":
                        row.append(Tile.POWER_PELLET)

                    case " ":
                        row.append(Tile.EMPTY)

                    case "P":
                        if pacman_start is not None:
                            raise ValueError("Map contains multiple Pac-Man spawns")

                        pacman_start = (x, y)
                        row.append(Tile.EMPTY)

                    case "G":
                        ghost_spawns.append((x, y))
                        row.append(Tile.EMPTY)

                    case _:
                        raise ValueError(
                            f"Unknown map character {char!r} at ({x}, {y})"
                        )

            tiles.append(row)

        if pacman_start is None:
            raise ValueError("Map does not contain a Pac-Man spawn")

        return cls(tiles=tiles, pacman_start=pacman_start, ghost_spawns=ghost_spawns)

    def to_lines(self) -> list[str]:
        char_for_tile = {
            Tile.WALL: "#",
            Tile.DOT: ".",
            Tile.POWER_PELLET: "O",
            Tile.EMPTY: " ",
        }
        lines = ["".join(char_for_tile[tile] for tile in row) for row in self.tiles]

        px, py = self.pacman_start
        lines[py] = lines[py][:px] + "P" + lines[py][px + 1 :]

        for gx, gy in self.ghost_spawns:
            lines[gy] = lines[gy][:gx] + "G" + lines[gy][gx + 1 :]

        return lines

    def save(self, path: Path) -> None:
        path.write_text("\n".join(self.to_lines()) + "\n")

    def is_walkable(self, x: int, y: int) -> bool:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return self.tiles[y][x] != Tile.WALL

    def eat_tile(self, x: int, y: int) -> Tile | None:
        tile = self.tiles[y][x]
        if tile in (Tile.DOT, Tile.POWER_PELLET):
            self.tiles[y][x] = Tile.EMPTY
            return tile
        return None

    @property
    def remaining_dots(self) -> int:
        return sum(
            row.count(Tile.DOT) + row.count(Tile.POWER_PELLET) for row in self.tiles
        )

    def get_layout(self, screen: pygame.Surface) -> MapLayout:
        width, height = screen.get_size()

        tile_size = min(width // self.width, height // self.height)

        map_width = self.width * tile_size
        map_height = self.height * tile_size

        offset_x = (width - map_width) // 2
        offset_y = (height - map_height) // 2

        return MapLayout(tile_size=tile_size, offset_x=offset_x, offset_y=offset_y)

    def draw(self, screen: pygame.Surface, layout: MapLayout | None = None) -> None:
        if layout is None:
            layout = self.get_layout(screen)

        for y, row in enumerate(self.tiles):
            for x, tile in enumerate(row):
                top_left = layout.to_pixel(x, y)
                rect = pygame.Rect(
                    top_left[0],
                    top_left[1],
                    layout.tile_size,
                    layout.tile_size,
                )

                self._draw_tile(screen, tile, rect, layout.tile_size)

    @staticmethod
    def _draw_tile(
        screen: pygame.Surface,
        tile: Tile,
        rect: pygame.Rect,
        tile_size: int,
    ) -> None:
        if tile == Tile.WALL:
            pygame.draw.rect(
                screen,
                (30, 30, 200),
                rect,
            )
        elif tile == Tile.DOT:
            pygame.draw.circle(
                screen,
                (255, 255, 255),
                rect.center,
                max(2, tile_size // 10),
            )
        elif tile == Tile.POWER_PELLET:
            pygame.draw.circle(
                screen,
                (255, 255, 255),
                rect.center,
                max(4, int(tile_size // 10 * 1.8)),
            )
