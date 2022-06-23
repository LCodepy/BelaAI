from typing import Tuple

import pygame

from bela.game.utils.colors import *

pygame.font.init()


class Label:

    def __init__(self, display: pygame.Surface, position: Tuple[int, int], size: Tuple[int, int], font, text: str = "",
                 font_color: Color = Colors.black, bold: bool = False, text_orientation: str = "center", padding: int = 10):
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

        line = 0
        for word in words:
            if (
                self.font.render(
                    self.lines[line] + word, self.bold, self.font_color.c
                ).get_width()
                > self.size[0]
            ):
                self.lines.append("")
                line += 1
            self.lines[line] += word + " "

        self.lines = list(filter(lambda l: l, self.lines))

    def set_text(self, text: str):
        self.text = text
        self.update_text()

    def get_text(self, text: str = None):
        return self.font.render(
            text or self.text, self.bold, self.font_color.c
        )

    """-------------------------------------{Updating}--------------------------------------------"""

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
