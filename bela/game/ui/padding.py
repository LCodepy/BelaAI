from typing import Tuple

import pygame

from bela.game.events.events import EventHandler
from bela.game.ui.ui_object import UIObject
from bela.game.utils.colors import Color


class Padding(UIObject):

    def __init__(self, display: pygame.Surface, position: Tuple[int, int], size: Tuple[int, int],
                 color: Color = None, border_color: Color = None, border_width: int = 2,
                 border_radius: int = 0, center_x: bool = True, center_y: bool = True) -> None:
        super().__init__(display, position, size, 0)
        self.display = display
        self.position = position
        self.w, self.h = size
        self.color = color
        self.border_color = border_color
        self.border_width = border_width
        self.border_radius = border_radius
        self.center_x = center_x
        self.center_y = center_y

        if not center_x:
            self.x += self.w // 2
        if not center_y:
            self.y += self.h // 2

        self.rect = pygame.Rect(self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)

        self.hovering = False
        self.clicked = False

    def update(self, event_handler: EventHandler) -> None:
        self.hovering = False
        self.clicked = False

        if self.rect.collidepoint(event_handler.get_pos()):
            self.hovering = True

            if event_handler.presses["left"]:
                self.clicked = True

    def render(self) -> None:
        if self.color:
            pygame.draw.rect(self.display, self.color, self.rect, border_radius=self.border_radius)
        if self.border_color:
            pygame.draw.rect(
                self.display, self.border_color, self.rect, width=self.border_width, border_radius=self.border_radius
            )

    def update_vars(self) -> None:
        if not self.center_x:
            self.x += self.w // 2
        if not self.center_y:
            self.y += self.h // 2

        self.rect = pygame.Rect(self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)

    def move(self, x: int = None, y: int = None, cx: bool = True, cy: bool = True) -> None:
        if x is not None:
            self.x = x
            if not cx:
                self.x += self.w // 2
        if y is not None:
            self.y = y
            if not cy:
                self.y += self.h // 2

        self.rect.x = self.x
        self.rect.y = self.y

    def get_size(self) -> Tuple[int, int]:
        return self.w, self.h

    def get_center(self) -> Tuple[int, int]:
        return self.rect.center

    def set_size(self, size: Tuple[int, int]) -> None:
        self.w, self.h = size

    def set_display(self, surface: pygame.Surface) -> None:
        self.display = surface

