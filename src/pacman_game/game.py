import pygame

from .game_state import GameState
from .screens.game_over_screen import GameOverScreen
from .screens.game_screen import GameScreen
from .screens.main_menu_screen import MainMenuScreen
from .screens.screen import Screen
from .screens.win_screen import WinScreen


class Game:
    def __init__(self, init_width: int, init_height: int):
        pygame.init()
        self.width: int = init_width
        self.height: int = init_height
        self.window: pygame.Surface | None = None
        self.state: GameState = GameState.MAIN_MENU
        self._menu_screen: Screen = MainMenuScreen()
        self._screens: dict[GameState, Screen] = {
            GameState.MAIN_MENU: self._menu_screen,
        }

    @property
    def current_screen(self) -> Screen:
        return self._screens[self.state]

    def initialize_window(self):
        pygame.init()
        self.window = pygame.display.set_mode(
            (self.width, self.height), pygame.RESIZABLE
        )
        pygame.display.set_caption("Pacman Game")

    def _transition_to(self, next_state: GameState) -> bool:
        if next_state is GameState.QUIT:
            return False

        if next_state is GameState.PLAYING:
            self._screens[GameState.PLAYING] = GameScreen()
        elif next_state is GameState.GAME_OVER:
            self._screens[GameState.GAME_OVER] = GameOverScreen(
                score=self.current_screen.score
            )
        elif next_state is GameState.WIN:
            self._screens[GameState.WIN] = WinScreen(score=self.current_screen.score)

        self.state = next_state
        return True

    def handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.size
                self.window = pygame.display.set_mode(
                    (self.width, self.height), pygame.RESIZABLE
                )
                continue

            next_state = self.current_screen.handle_event(event)
            if next_state is not None and not self._transition_to(next_state):
                return False
        return True

    def update(self, dt: float) -> bool:
        next_state = self.current_screen.update(dt)
        if next_state is not None:
            return self._transition_to(next_state)
        return True

    def draw(self) -> None:
        if not self.window:
            return

        self.window.fill((0, 0, 0))
        self.current_screen.draw(self.window)

    def game_loop(self):
        clock = pygame.time.Clock()
        running = True
        self.initialize_window()
        while running:
            running = self.handle_events()
            dt = clock.tick(60) / 1000.0
            if running:
                running = self.update(dt)
            self.draw()
            pygame.display.flip()
        pygame.quit()


def main() -> None:
    Game(800, 600).game_loop()
