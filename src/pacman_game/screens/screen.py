from abc import ABC, abstractmethod

import pygame

from ..game_state import GameState


class Screen(ABC):
    score: int = 0

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> GameState | None:
        """Process one pygame event.

        Return a GameState to request switching to it, or None to stay.
        """

    @abstractmethod
    def update(self, dt: float) -> GameState | None:
        """Advance one frame.

        Return a GameState to request switching to it, or None to stay.
        """

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None: ...
