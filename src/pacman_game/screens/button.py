from dataclasses import dataclass, field

import pygame

from ..game_state import GameState

BUTTON_COLOR = (30, 30, 200)
BUTTON_HOVER_COLOR = (60, 60, 255)
BUTTON_TEXT_COLOR = (255, 255, 255)


@dataclass
class Button:
    label: str
    target_state: GameState
    rect: pygame.Rect = field(default_factory=lambda: pygame.Rect(0, 0, 0, 0))

    def contains(self, point: tuple[int, int]) -> bool:
        return self.rect.collidepoint(point)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        hovered = self.contains(pygame.mouse.get_pos())
        color = BUTTON_HOVER_COLOR if hovered else BUTTON_COLOR
        pygame.draw.rect(surface, color, self.rect)

        text = font.render(self.label, True, BUTTON_TEXT_COLOR)
        surface.blit(text, text.get_rect(center=self.rect.center))
