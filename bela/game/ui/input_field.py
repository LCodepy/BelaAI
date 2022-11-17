import string
import time
from typing import Optional, Tuple

import pygame

from bela.game.events.events import EventHandler
from bela.game.ui.label import Label
from bela.game.ui.ui_object import UIObject
from bela.game.utils.colors import Color, Colors


class InputField(UIObject):

    def __init__(self, display: pygame.Surface, position: Tuple[int, int], size: Tuple[int, int], font,
                 center_x: bool = True, center_y: bool = True, hint: str = None,
                 color: Optional[Color] = Colors.dark_red, font_color: Color = Colors.black, bold: bool = False,
                 padding: int = 0, border_color: Color = None, border_radius: int = 0, border_width: int = 2,
                 text_underline: bool = True, max_length: int = None, text_orientation: str = "left") -> None:

        super().__init__(display, position, size, padding, border_color, border_radius, border_width)

        self.display = display
        self.x, self.y = position
        self.w, self.h = size
        self.hint = hint
        self.font = font
        self.color = color
        self.font_color = font_color
        self.bold = bold
        self.padding = padding
        self.border_color = border_color
        self.border_radius = border_radius
        self.border_width = border_width
        self.text_underline = text_underline
        self.max_length = max_length
        self.center_x = center_x
        self.center_y = center_y
        self.text_orientation = text_orientation

        self.special_chars = "_.@čćđšžČĆĐŠŽ"

        self.hint_font_color = self.font_color.darker(100)
        self.text = ""
        self.focused = False

        self.label = Label(self.display, (self.x if center_x else self.x + size[0] // 2, self.y), size, font, text=hint,
                           font_color=self.hint_font_color, bold=bold, text_orientation=text_orientation,
                           padding=padding)

        if self.padding is not None:
            self.w += max(self.padding - (self.w - self.label.get_size()[0]), 0)
            self.h += max(self.padding - (self.h - self.label.get_size()[1]), 0)

        if not center_x:
            self.x += self.w // 2
        if not center_y:
            self.y += self.h // 2

        self.rect = pygame.Rect(self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)

        self.last_drawn_cursor = 0
        self.cursor_show_time = 0.8
        self.show_cursor = False

    def update_vars(self) -> None:
        self.hint_font_color = self.font_color.darker(100)

        self.label = Label(self.display, (self.x if self.center_x else self.x + self.w // 2, self.y), (self.w, self.h),
                           self.font, text=self.hint, font_color=self.hint_font_color, bold=self.bold,
                           text_orientation=self.text_orientation, padding=self.padding)

        if self.padding is not None:
            self.w += max(self.padding - (self.w - self.label.get_size()[0]), 0)
            self.h += max(self.padding - (self.h - self.label.get_size()[1]), 0)

        if not self.center_x:
            self.x += self.w // 2
        if not self.center_y:
            self.y += self.h // 2

        self.rect = pygame.Rect(self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)

    def update(self, event_handler: EventHandler) -> None:
        pos = event_handler.get_pos()

        if time.time() - self.last_drawn_cursor > self.cursor_show_time:
            self.show_cursor = not self.show_cursor
            self.last_drawn_cursor = time.time()

        if event_handler.presses["left"]:
            self.focused = self.rect.collidepoint(*pos)

        if self.focused:
            for char in event_handler.unicode_keys.keys():
                if char not in string.ascii_uppercase + string.ascii_lowercase + string.digits + self.special_chars:
                    continue
                if self.max_length and len(self.text) + 1 <= self.max_length:
                    self.text += char

            for key in event_handler.keys.keys():
                if key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                if key in (pygame.K_RETURN, pygame.K_TAB):
                    self.focused = False

        self.label.set_text(self.text or self.hint)
        self.label.font_color = self.font_color if self.text else self.hint_font_color

    def render(self) -> None:
        if self.color is None:
            return

        surf = pygame.Surface(self.rect.size, pygame.SRCALPHA)

        pygame.draw.rect(surf, self.color.c, [0, 0, self.rect.w, self.rect.h], width=0,
                         border_radius=self.border_radius)
        if self.border_color:
            pygame.draw.rect(surf, self.border_color.c, [0, 0, self.rect.w, self.rect.h],
                             width=self.border_width, border_radius=self.border_radius)

        if self.text_underline:
            pygame.draw.line(
                surf, (self.border_color or self.color).c,
                (10, self.h // 2 + self.label.get_size()[1] // 2),
                (self.rect.w - 10, self.h // 2 + self.label.get_size()[1] // 2), self.border_width
            )

        self.display.blit(surf, (self.rect.x, self.rect.y))

        self.label.render()
        self.render_cursor()

    def render_cursor(self) -> None:
        if not self.focused:
            return

        if self.show_cursor:
            label_w = self.label.get_size()[0] if self.text else 0
            pygame.draw.line(
                self.display, self.font_color.c,
                (self.x - self.w // 2 + self.padding + label_w, self.y - self.label.get_size()[1] // 2),
                (self.x - self.w // 2 + self.padding + label_w, self.y + self.label.get_size()[1] // 2)
            )

    def move(self, x: int = None, y: int = None, cx: bool = True, cy: bool = True) -> None:
        self.x = x or self.rect.x
        self.y = y or self.rect.y
        if x and not cx:
            self.x += self.w // 2
        if y and not cy:
            self.y += self.h // 2
        self.rect.x = self.x
        self.rect.y = self.y

    def get_size(self) -> Tuple[int, int]:
        return self.rect.size
