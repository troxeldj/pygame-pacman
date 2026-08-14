from pathlib import Path

import pygame

from ..entity.entity import Entity
from ..entity.ghost import Ghost
from ..entity.pacman import Pacman
from ..game_map import GameMap
from ..game_state import GameState
from ..orientation import Orientation
from ..position import Position
from ..tile import Tile
from .screen import Screen

_GHOST_COLORS = ["blinky", "pinky", "inky", "clyde"]
_STARTING_LIVES = 3
_DOT_SCORE = 10
_READY_DURATION = 3.0
_READY_COLOR = (255, 255, 0)
_PAUSE_HINT_COLOR = (255, 255, 255)
_POWER_DURATION = 8.0
_GHOST_EAT_SCORE = 200
_GHOST_RESPAWN_DELAY = 2.0


class GameScreen(Screen):
    def __init__(self) -> None:
        levels_dir = Path(__file__).parent.parent.parent.parent / "assets" / "levels"
        self._levels: list[Path] = sorted(levels_dir.glob("*.txt"))
        self._lives = _STARTING_LIVES
        self.score = 0
        self._hud_font = pygame.font.SysFont(None, 28)
        self._ready_font = pygame.font.SysFont(None, 48)
        self._pause_hint_font = pygame.font.SysFont(None, 24)
        self._paused = False

        self._load_level(0)

    def _load_level(self, index: int) -> None:
        self._level_index = index
        self._game_map: GameMap = GameMap.load(self._levels[index])
        self._reset_entities()
        self._ready_timer = _READY_DURATION
        self._frightened_timer = 0.0

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

    def _respawn_ghost(self, ghost: Ghost) -> None:
        px, py = self._pacman.position.x, self._pacman.position.y
        spawn_x, spawn_y = max(
            self._game_map.ghost_spawns,
            key=lambda spawn: (spawn[0] - px) ** 2 + (spawn[1] - py) ** 2,
        )
        ghost.position = Position(x=spawn_x, y=spawn_y)
        ghost.orientation = Orientation.LEFT
        ghost.set_frightened(False)
        ghost.clear_respawn_delay()

    def handle_event(self, event: pygame.event.Event) -> GameState | None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._paused = not self._paused
                return None

            if self._paused:
                if event.key == pygame.K_m:
                    return GameState.MAIN_MENU
                return None

            if event.key in (pygame.K_UP, pygame.K_w):
                self._pacman.change_orientation(Orientation.UP)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._pacman.change_orientation(Orientation.DOWN)
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self._pacman.change_orientation(Orientation.LEFT)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._pacman.change_orientation(Orientation.RIGHT)
        return None

    def update(self, dt: float) -> GameState | None:
        if self._paused:
            return None

        if self._ready_timer > 0:
            self._ready_timer = max(0.0, self._ready_timer - dt)
            return None

        for ghost in self._ghosts:
            if ghost.pending_respawn:
                ghost.respawn_timer -= dt
                if ghost.respawn_timer <= 0:
                    self._respawn_ghost(ghost)

        for ghost in self._ghosts:
            ghost.update_target(self._pacman, self._game_map)

        for entity in self._entities:
            entity.update(dt, self._game_map)

        if self._frightened_timer > 0:
            self._frightened_timer = max(0.0, self._frightened_timer - dt)
            if self._frightened_timer == 0:
                for ghost in self._ghosts:
                    ghost.set_frightened(False)

        eaten = self._game_map.eat_tile(
            self._pacman.position.x, self._pacman.position.y
        )
        if eaten is Tile.DOT:
            self.score += _DOT_SCORE
        elif eaten is Tile.POWER_PELLET:
            self.score += _DOT_SCORE
            self._frightened_timer = _POWER_DURATION
            for ghost in self._ghosts:
                ghost.set_frightened(True)

        for ghost in self._ghosts:
            if ghost.pending_respawn:
                continue

            if (ghost.position.x, ghost.position.y) == (
                self._pacman.position.x,
                self._pacman.position.y,
            ):
                if ghost.frightened:
                    self.score += _GHOST_EAT_SCORE
                    ghost.set_frightened(False)
                    ghost.start_respawn_delay(_GHOST_RESPAWN_DELAY)
                    continue

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

        if self._paused:
            self._draw_paused(surface)
        elif self._ready_timer > 0:
            self._draw_ready(surface)

    def _draw_ready(self, surface: pygame.Surface) -> None:
        text = self._ready_font.render("Ready!", True, _READY_COLOR)
        rect = text.get_rect(center=surface.get_rect().center)
        surface.blit(text, rect)

    def _draw_paused(self, surface: pygame.Surface) -> None:
        center = surface.get_rect().center
        text = self._ready_font.render("Paused", True, _READY_COLOR)
        rect = text.get_rect(center=center)
        surface.blit(text, rect)

        hint = self._pause_hint_font.render(
            "Esc to Resume - M for Main Menu", True, _PAUSE_HINT_COLOR
        )
        hint_rect = hint.get_rect(center=(center[0], rect.bottom + 20))
        surface.blit(hint, hint_rect)

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
