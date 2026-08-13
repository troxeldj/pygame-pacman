import pygame

from ..game_state import GameState
from .button import Button
from .screen import Screen

_TITLE_COLOR = (255, 255, 0)

_BUTTON_WIDTH = 200
_BUTTON_HEIGHT = 60
_BUTTON_SPACING = 20


class MainMenuScreen(Screen):
    def __init__(self) -> None:
        self._title_font = pygame.font.SysFont(None, 72)
        self._button_font = pygame.font.SysFont(None, 40)
        self._buttons = [
            Button(label="Play", target_state=GameState.PLAYING),
            Button(label="Quit", target_state=GameState.QUIT),
        ]

    def _layout_buttons(self, surface: pygame.Surface) -> None:
        width, height = surface.get_size()
        total_height = len(self._buttons) * _BUTTON_HEIGHT + (
            len(self._buttons) - 1
        ) * _BUTTON_SPACING
        top = height // 2 - total_height // 2

        for i, button in enumerate(self._buttons):
            button.rect = pygame.Rect(
                width // 2 - _BUTTON_WIDTH // 2,
                top + i * (_BUTTON_HEIGHT + _BUTTON_SPACING),
                _BUTTON_WIDTH,
                _BUTTON_HEIGHT,
            )

    def handle_event(self, event: pygame.event.Event) -> GameState | None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self._buttons:
                if button.contains(event.pos):
                    return button.target_state
        return None

    def update(self, dt: float) -> GameState | None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        self._layout_buttons(surface)

        title = self._title_font.render("PACMAN", True, _TITLE_COLOR)
        width, _ = surface.get_size()
        top = self._buttons[0].rect.top - title.get_height() - 40
        surface.blit(title, title.get_rect(centerx=width // 2, top=top))

        for button in self._buttons:
            button.draw(surface, self._button_font)
