import pygame

from ..game_state import GameState
from .button import Button
from .screen import Screen

_TITLE_COLOR = (220, 30, 30)

_BUTTON_WIDTH = 220
_BUTTON_HEIGHT = 60


class GameOverScreen(Screen):
    def __init__(self, score: int = 0) -> None:
        self._score = score
        self._title_font = pygame.font.SysFont(None, 72)
        self._score_font = pygame.font.SysFont(None, 36)
        self._button_font = pygame.font.SysFont(None, 40)
        self._button = Button(label="Main Menu", target_state=GameState.MAIN_MENU)

    def _layout_button(self, surface: pygame.Surface) -> None:
        width, height = surface.get_size()
        self._button.rect = pygame.Rect(
            width // 2 - _BUTTON_WIDTH // 2,
            height // 2 + 20,
            _BUTTON_WIDTH,
            _BUTTON_HEIGHT,
        )

    def handle_event(self, event: pygame.event.Event) -> GameState | None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._button.contains(event.pos):
                return self._button.target_state
        return None

    def update(self, dt: float) -> GameState | None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        self._layout_button(surface)
        width, _ = surface.get_size()

        title = self._title_font.render("GAME OVER", True, _TITLE_COLOR)
        top = self._button.rect.top - title.get_height() - 80
        surface.blit(title, title.get_rect(centerx=width // 2, top=top))

        score_text = self._score_font.render(
            f"Score: {self._score}", True, (255, 255, 255)
        )
        score_top = title.get_rect(centerx=width // 2, top=top).bottom + 20
        surface.blit(score_text, score_text.get_rect(centerx=width // 2, top=score_top))

        self._button.draw(surface, self._button_font)
