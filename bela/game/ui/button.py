from typing import Tuple

import pygame

from bela.game.ui.label import Label
from bela.game.utils.assets import Assets
from bela.game.utils.colors import Color


class Button:

    def __init__(self, display, center, size, font, center_x: bool = True, center_y: bool = True, text: str = None,
                 img: pygame.Surface = None,
                 font_color: Tuple = (0, 0, 0), bold: bool = False, text_orientation: str = "center",
                 padding: int = 20) -> None:
        self.display = display
        self.x, self.y = center
        self.w, self.h = size
        self.text = text
        self.font = font
        self.img = img
        self.font_color = font_color
        self.bold = bold
        self.text_orientation = text_orientation
        self.padding = padding
        self.assets = Assets()

        if not center_x:
            self.x += self.w // 2
        if not center_y:
            self.y += self.h // 2

        if self.img is not None:
            self.img = pygame.transform.scale(img, size)

        self.rect = pygame.Rect(self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)
        self.label = Label(display, (self.x, self.y), size, font, text=text, font_color=font_color, bold=bold,
                           text_orientation=text_orientation, padding=padding)

    def set_text(self, text: str) -> None:
        self.text = text
        self.label.set_text(text)

    def render(self) -> None:
        if self.img is None:
            self.render_non_image()
        else:
            self.render_image()

        self.label.render()

        pygame.draw.rect(self.img, (255, 0, 0), self.rect, 1)

    def render_non_image(self) -> None:
        pygame.draw.rect(self.display, Color.red, self.rect)

    def render_image(self) -> None:
        self.display.blit(self.img, (self.rect.x, self.rect.y))
