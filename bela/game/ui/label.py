from typing import Tuple, Union

import pygame

from bela.game.events.events import EventHandler
from bela.game.ui.ui_object import UIObject
from bela.game.utils.colors import *

pygame.font.init()


class Label(UIObject):

    def __init__(self, display: pygame.Surface, position: Tuple[int, int], size: Union[Tuple[int, int], str], font,
                 text: str = "", font_color: Color = Colors.black, bold: bool = False,
                 text_orientation: str = "center", padding: int = 10):

        super().__init__(display, position, size, padding)

        self.display = display
        self.x, y = position
        self.size = size
        self.text = text
        self.font_color = font_color
        self.bold = bold
        self.font = font
        self.text_orientation = text_orientation
        self.padding = padding

        self.is_hovering = False

        if self.size == "fit":
            self.size = (float("inf"), float("inf"))

        self.lines = [""]
        self.update_text()

    def update_vars(self) -> None:
        if self.size == "fit":
            self.size = (float("inf"), float("inf"))

        self.lines = [""]
        self.update_text()

    def update(self, event_handler: EventHandler) -> None:
        self.is_hovering = False

        w, h = self.size
        rect = pygame.Rect(self.x - w // 2, self.y - h // 2, w, h)
        if rect.collidepoint(event_handler.get_pos()):
            self.is_hovering = True

    def render(self):
        for i, text in enumerate(self.lines):
            t = self.get_text(text=text)

            if self.text_orientation == "left":
                x = self.x + self.padding - self.size[0] // 2
            elif self.text_orientation == "center":
                x = self.x - t.get_rect().w // 2
            else:
                x = self.x + self.size[0] // 2 - t.get_rect().w - self.padding

            self.display.blit(t, (x, self.y - (len(self.lines) * (t.get_rect().h + 2) - 2) // 2
                                  + (t.get_rect().h + 2) * i))

    def update_text(self):
        words = self.text.split(" ")
        self.lines = [""]

        line = 0
        for word in words:
            if word == "\n":
                self.lines[line] = self.lines[line][:-1]
                self.lines.append("")
                line += 1
                continue
            if (
                self.font.render(self.lines[line], self.bold, self.font_color.c).get_width() > self.size[0]
                and self.lines[line]
            ):
                self.lines[line] = self.lines[line][:-1]
                self.lines.append("")
                line += 1
            self.lines[line] += word + " "
        self.lines[line] = self.lines[line][:-1]

        self.lines = list(filter(lambda l: l, self.lines))

    def set_text(self, text: str):
        self.text = text
        self.update_text()

    def set_surface(self, surf: pygame.Surface) -> None:
        self.display = surf

    def get_text(self, text: str = None):
        return self.font.render(
            text or self.text, self.bold, self.font_color.c
        )

    def get_size(self) -> Tuple[int, int]:
        x_size = 0
        y_size = 0
        for i, text in enumerate(self.lines):
            t = self.get_text(text=text)

            x_size = max(t.get_rect().w, x_size)
            y_size = (len(self.lines) * (t.get_rect().h + 2) - 2)

        return x_size, y_size

    def get_pos(self) -> Tuple[int, int]:
        return self.x, self.y

    def get_center(self) -> Tuple[int, int]:
        return self.x, self.y

    def set_size(self, size: Tuple[int, int]) -> None:
        self.size = size

    def move(self, x: int = None, y: int = None, cx: bool = True, cy: bool = True) -> None:
        self.x = x or self.x
        self.y = y or self.y
        if x and not cx:
            self.x += self.w // 2
        if y and not cy:
            self.y += self.h // 2

    @staticmethod
    def render_text(surface, text, pos, font, color, bold: bool = False, centered: bool = True, alpha: int = -1):
        rendered = font.render(text, bold, color)
        if alpha >= 0:
            transparent = pygame.Surface(rendered.get_size(), pygame.SRCALPHA)
            transparent.blit(rendered, (0, 0))
            transparent.set_alpha(alpha)
            surface.blit(transparent, (pos[0] - rendered.get_rect().w // 2 * centered,
                                       pos[1] - rendered.get_rect().h // 2 * centered))
        else:
            surface.blit(rendered, (pos[0] - rendered.get_rect().w // 2 * centered,
                                    pos[1] - rendered.get_rect().h // 2 * centered))
