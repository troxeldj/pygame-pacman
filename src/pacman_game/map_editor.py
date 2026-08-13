import argparse
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

import pygame

from .game_map import GameMap, MapLayout
from .tile import Tile

_ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"
_DEFAULT_OUTPUT = _ASSETS_DIR / "levels" / "custom_map.txt"

_TOOLBAR_HEIGHT = 64
_SWATCH_SIZE = 48
_SWATCH_SPACING = 12
_STATUS_HEIGHT = 28

_BG_COLOR = (0, 0, 0)
_TOOLBAR_COLOR = (20, 20, 20)
_GRID_LINE_COLOR = (40, 40, 40)
_SELECTED_COLOR = (255, 255, 0)
_STATUS_COLOR = (255, 255, 255)


class EditorTool(Enum):
    WALL = auto()
    DOT = auto()
    EMPTY = auto()
    PACMAN_SPAWN = auto()
    GHOST_SPAWN = auto()


_TOOL_LABELS = {
    EditorTool.WALL: "Wall",
    EditorTool.DOT: "Dot",
    EditorTool.EMPTY: "Empty",
    EditorTool.PACMAN_SPAWN: "Pacman",
    EditorTool.GHOST_SPAWN: "Ghost",
}

_TOOL_TO_TILE = {
    EditorTool.WALL: Tile.WALL,
    EditorTool.DOT: Tile.DOT,
    EditorTool.EMPTY: Tile.EMPTY,
}


@dataclass
class _Swatch:
    tool: EditorTool
    rect: pygame.Rect = field(default_factory=lambda: pygame.Rect(0, 0, 0, 0))

    def contains(self, point: tuple[int, int]) -> bool:
        return self.rect.collidepoint(point)


class MapEditor:
    def __init__(self, width: int, height: int, output_path: Path) -> None:
        self.grid_width = width
        self.grid_height = height
        self.output_path = output_path

        self.tiles: list[list[Tile]] = [
            [Tile.EMPTY for _ in range(width)] for _ in range(height)
        ]
        self.pacman_pos: tuple[int, int] | None = None
        self.ghost_positions: list[tuple[int, int]] = []

        self.selected_tool = EditorTool.WALL
        self._painting = False
        self._last_painted: tuple[int, int] | None = None
        self.status_message = "Left-click/drag to paint. Press E to export."

        self._label_font = pygame.font.SysFont(None, 22)
        self._status_font = pygame.font.SysFont(None, 22)

        self._pacman_preview = pygame.image.load(
            _ASSETS_DIR / "pacman-right" / "1.png"
        )
        self._ghost_preview = pygame.image.load(_ASSETS_DIR / "ghosts" / "blinky.png")

        self._swatches = [_Swatch(tool=tool) for tool in EditorTool]

    @classmethod
    def from_existing_map(cls, game_map: GameMap, output_path: Path) -> "MapEditor":
        editor = cls(game_map.width, game_map.height, output_path)
        editor.tiles = [row[:] for row in game_map.tiles]
        editor.pacman_pos = game_map.pacman_start
        editor.ghost_positions = list(game_map.ghost_spawns)
        editor.status_message = f"Loaded {output_path.name}"
        return editor

    # -- layout -----------------------------------------------------------

    def _layout_swatches(self) -> None:
        x = _SWATCH_SPACING
        y = (_TOOLBAR_HEIGHT - _SWATCH_SIZE) // 2
        for swatch in self._swatches:
            swatch.rect = pygame.Rect(x, y, _SWATCH_SIZE, _SWATCH_SIZE)
            x += _SWATCH_SIZE + _SWATCH_SPACING

    def _grid_layout(self, surface: pygame.Surface) -> MapLayout:
        width, height = surface.get_size()
        grid_area_height = max(1, height - _TOOLBAR_HEIGHT - _STATUS_HEIGHT)

        tile_size = max(
            1, min(width // self.grid_width, grid_area_height // self.grid_height)
        )
        map_width = self.grid_width * tile_size
        map_height = self.grid_height * tile_size

        offset_x = (width - map_width) // 2
        offset_y = _TOOLBAR_HEIGHT + (grid_area_height - map_height) // 2

        return MapLayout(tile_size=tile_size, offset_x=offset_x, offset_y=offset_y)

    def _cell_at(
        self, pos: tuple[int, int], layout: MapLayout
    ) -> tuple[int, int] | None:
        x, y = pos
        if layout.tile_size <= 0:
            return None
        gx = (x - layout.offset_x) // layout.tile_size
        gy = (y - layout.offset_y) // layout.tile_size
        if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height:
            return int(gx), int(gy)
        return None

    # -- editing ------------------------------------------------------------

    def _apply_tool(self, cell: tuple[int, int]) -> None:
        x, y = cell

        if cell == self.pacman_pos:
            self.pacman_pos = None
        if cell in self.ghost_positions:
            self.ghost_positions.remove(cell)

        if self.selected_tool in _TOOL_TO_TILE:
            self.tiles[y][x] = _TOOL_TO_TILE[self.selected_tool]
        elif self.selected_tool is EditorTool.PACMAN_SPAWN:
            self.tiles[y][x] = Tile.EMPTY
            self.pacman_pos = cell
        elif self.selected_tool is EditorTool.GHOST_SPAWN:
            self.tiles[y][x] = Tile.EMPTY
            self.ghost_positions.append(cell)

    # -- events ---------------------------------------------------------

    def handle_event(self, event: pygame.event.Event, surface: pygame.Surface) -> bool:
        """Process one pygame event. Returns False if the editor should quit."""
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            self.export()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for swatch in self._swatches:
                if swatch.contains(event.pos):
                    self.selected_tool = swatch.tool
                    return True

            layout = self._grid_layout(surface)
            cell = self._cell_at(event.pos, layout)
            if cell is not None:
                self._apply_tool(cell)
                self._painting = True
                self._last_painted = cell

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._painting = False
            self._last_painted = None

        elif event.type == pygame.MOUSEMOTION and self._painting:
            layout = self._grid_layout(surface)
            cell = self._cell_at(event.pos, layout)
            if cell is not None and cell != self._last_painted:
                self._apply_tool(cell)
                self._last_painted = cell

        return True

    # -- export -----------------------------------------------------------

    def _unreachable_count(self) -> int:
        if self.pacman_pos is None:
            return 0

        def is_walkable(x: int, y: int) -> bool:
            return (
                0 <= x < self.grid_width
                and 0 <= y < self.grid_height
                and self.tiles[y][x] != Tile.WALL
            )

        start = self.pacman_pos
        seen = {start}
        queue = deque([start])
        while queue:
            x, y = queue.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if is_walkable(nx, ny) and (nx, ny) not in seen:
                    seen.add((nx, ny))
                    queue.append((nx, ny))

        total_walkable = sum(
            1
            for y in range(self.grid_height)
            for x in range(self.grid_width)
            if is_walkable(x, y)
        )
        return total_walkable - len(seen)

    def export(self) -> None:
        if self.pacman_pos is None:
            self.status_message = "Place a Pacman spawn before exporting"
            return

        game_map = GameMap(
            tiles=self.tiles,
            pacman_start=self.pacman_pos,
            ghost_spawns=self.ghost_positions,
        )
        game_map.save(self.output_path)

        unreachable = self._unreachable_count()
        if unreachable:
            self.status_message = (
                f"Saved to {self.output_path} (warning: {unreachable} "
                "tile(s) unreachable)"
            )
        else:
            self.status_message = f"Saved to {self.output_path}"

    # -- drawing ------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(_BG_COLOR)
        self._layout_swatches()
        self._draw_toolbar(surface)
        self._draw_grid(surface)
        self._draw_status(surface)

    def _draw_toolbar(self, surface: pygame.Surface) -> None:
        width, _ = surface.get_size()
        pygame.draw.rect(surface, _TOOLBAR_COLOR, pygame.Rect(0, 0, width, _TOOLBAR_HEIGHT))

        for swatch in self._swatches:
            self._draw_tool_icon(surface, swatch.tool, swatch.rect)

            if swatch.tool is self.selected_tool:
                pygame.draw.rect(surface, _SELECTED_COLOR, swatch.rect, width=3)

            label = self._label_font.render(
                _TOOL_LABELS[swatch.tool], True, _STATUS_COLOR
            )
            surface.blit(
                label, label.get_rect(centerx=swatch.rect.centerx, top=swatch.rect.bottom + 2)
            )

    def _draw_tool_icon(
        self, surface: pygame.Surface, tool: EditorTool, rect: pygame.Rect
    ) -> None:
        if tool in _TOOL_TO_TILE:
            GameMap._draw_tile(surface, _TOOL_TO_TILE[tool], rect, rect.width)
            if tool is EditorTool.EMPTY:
                pygame.draw.rect(surface, _GRID_LINE_COLOR, rect, width=1)
        elif tool is EditorTool.PACMAN_SPAWN:
            self._blit_preview(surface, self._pacman_preview, rect)
        elif tool is EditorTool.GHOST_SPAWN:
            self._blit_preview(surface, self._ghost_preview, rect)

    @staticmethod
    def _blit_preview(
        surface: pygame.Surface, image: pygame.Surface, rect: pygame.Rect
    ) -> None:
        scaled = pygame.transform.scale(image, (rect.width, rect.height))
        surface.blit(scaled, rect.topleft)

    def _draw_grid(self, surface: pygame.Surface) -> None:
        layout = self._grid_layout(surface)

        for y in range(self.grid_height):
            for x in range(self.grid_width):
                top_left = layout.to_pixel(x, y)
                rect = pygame.Rect(
                    top_left[0], top_left[1], layout.tile_size, layout.tile_size
                )
                GameMap._draw_tile(surface, self.tiles[y][x], rect, layout.tile_size)
                pygame.draw.rect(surface, _GRID_LINE_COLOR, rect, width=1)

        if self.pacman_pos is not None:
            top_left = layout.to_pixel(*self.pacman_pos)
            rect = pygame.Rect(top_left[0], top_left[1], layout.tile_size, layout.tile_size)
            self._blit_preview(surface, self._pacman_preview, rect)

        for ghost_pos in self.ghost_positions:
            top_left = layout.to_pixel(*ghost_pos)
            rect = pygame.Rect(top_left[0], top_left[1], layout.tile_size, layout.tile_size)
            self._blit_preview(surface, self._ghost_preview, rect)

    def _draw_status(self, surface: pygame.Surface) -> None:
        width, height = surface.get_size()
        bar_rect = pygame.Rect(0, height - _STATUS_HEIGHT, width, _STATUS_HEIGHT)
        pygame.draw.rect(surface, _TOOLBAR_COLOR, bar_rect)

        text = self._status_font.render(self.status_message, True, _STATUS_COLOR)
        surface.blit(text, (8, bar_rect.top + 4))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pacman map editor")
    parser.add_argument("--width", type=int, default=21, help="grid width (new map)")
    parser.add_argument("--height", type=int, default=15, help="grid height (new map)")
    parser.add_argument("--load", type=Path, default=None, help="existing level to edit")
    parser.add_argument(
        "--output", type=Path, default=_DEFAULT_OUTPUT, help="export path"
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    pygame.init()
    window = pygame.display.set_mode((900, 700), pygame.RESIZABLE)
    pygame.display.set_caption("Pacman Map Editor")

    if args.load is not None:
        editor = MapEditor.from_existing_map(GameMap.load(args.load), args.output)
    else:
        editor = MapEditor(args.width, args.height, args.output)

    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.VIDEORESIZE:
                window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                continue
            running = editor.handle_event(event, window)
            if not running:
                break

        editor.draw(window)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
