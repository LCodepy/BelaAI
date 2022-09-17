from typing import Tuple

import pygame

from bela.game.utils.colors import *

pygame.font.init()


class Label:

    def __init__(self, display: pygame.Surface, position: Tuple[int, int], size: Tuple[int, int], font, text: str = "",
                 font_color: Color = Colors.black, bold: bool = False, text_orientation: str = "center",
                 padding: int = 10):
        self.display = display
        self.position = position
        self.size = size
        self.text = text
        self.font_color = font_color
        self.bold = bold
        self.font = font
        self.text_orientation = text_orientation
        self.padding = padding

        self.lines = [""]
        self.update_text()

    def update_text(self):
        words = self.text.split()
        self.lines = [""]

        line = 0
        for word in words:
            if (
                self.font.render(self.lines[line] + word, self.bold, self.font_color.c).get_width() > self.size[0]
                and self.lines[line]
            ):
                self.lines.append("")
                line += 1
                self.lines[line-1] = self.lines[line-1][:-1]
            self.lines[line] += word + " "
        self.lines[line - 1] = self.lines[line - 1][:-1]

        self.lines = list(filter(lambda l: l, self.lines))

    def set_text(self, text: str):
        self.text = text
        self.update_text()

    def get_text(self, text: str = None):
        return self.font.render(
            text or self.text, self.bold, self.font_color.c
        )

    def move(self, x: int = None, y: int = None) -> None:
        self.position = (x or self.position[0], y or self.position[1])

    def render(self):
        for i, text in enumerate(self.lines):
            t = self.get_text(text=text)

            if self.text_orientation == "left":
                x = self.position[0] + self.padding - self.size[0] // 2
            elif self.text_orientation == "center":
                x = self.position[0] - t.get_rect().w // 2
            else:
                x = self.position[0] + self.size[0] // 2 - t.get_rect().w - self.padding

            self.display.blit(t, (x, self.position[1] - (len(self.lines) * (t.get_rect().h + 2) - 2) // 2
                                  + (t.get_rect().h + 2) * i))

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
