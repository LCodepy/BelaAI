from __future__ import annotations

import time
from typing import Callable, Optional
import pygame

from bela.game.events.events import EventHandler
from bela.game.ui.label import Label
from bela.game.utils.assets import Assets
from bela.game.utils.colors import *


class Button:

    def __init__(self, display, center, size, font, center_x: bool = True, center_y: bool = True, text: str = None,
                 img: pygame.Surface = None, color: Optional[Color] = Colors.dark_red,
                 font_color: Color = Colors.black, bold: bool = False, text_orientation: str = "center",
                 padding: Optional[int] = None, border_color: Color = None, border_radius: int = 0,
                 border_width: int = 2) -> None:
        self.display = display
        self.x, self.y = center
        self.text = text
        self.font = font
        self.img = img
        self.color = color
        self.font_color = font_color
        self.bold = bold
        self.text_orientation = text_orientation
        self.padding = padding
        self.border_color = border_color
        self.border_radius = border_radius
        self.border_width = border_width
        self.assets = Assets()

        self.label = Label(display, (self.x, self.y), size, font, text=text, font_color=font_color, bold=bold,
                           text_orientation=text_orientation, padding=padding)

        if isinstance(size, str):
            if size == "fit":
                self.w, self.h = self.label.get_size()
        else:
            self.w, self.h = size

        if self.padding is not None:
            self.w += max(self.padding - (self.w - self.label.get_size()[0]), 0)
            self.h += max(self.padding - (self.h - self.label.get_size()[1]), 0)

        if not center_x:
            self.x += self.w // 2
        if not center_y:
            self.y += self.h // 2

        if self.img is not None:
            self.img = pygame.transform.scale(img, size)

        self.rect = pygame.Rect(self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)

        self.on_hover_listener = None
        self.on_click_listener = None
        self.on_hold_listener = None

        self.hover_class = None
        self.click_class = None
        self.hold_class = None

        self.hover_pass_self = False
        self.click_pass_self = False
        self.hold_pass_self = False

        self.is_hovering = False
        self.is_clicked = False
        self.is_held = False
        self.was_held = False

        self.last_hovered = False
        self.last_held = False

        self.disable_time = 0.1
        self.init = False
        self.init_time = 0

    def reinit(self) -> None:
        self.disable_time = 0.1
        self.init_time = 0
        self.init = False

    def set_text(self, text: str) -> None:
        self.text = text
        self.label.set_text(text)

    def update(self, event_handler: EventHandler) -> None:
        if not self.init:
            self.init = True
            self.init_time = time.time()
        if time.time() - self.init_time <= self.disable_time:
            return

        if self.color:
            if self.last_hovered and not self.is_hovering:  # e.i. on_exit()
                self.color = self.color.darker(50)
            elif not self.last_hovered and self.is_hovering:  # e.i. on_enter()
                self.color = self.color.brighter(50)

        self.last_hovered = self.is_hovering
        self.last_held = self.is_held

        self.is_clicked = False
        self.is_hovering = False
        self.is_held = False

        pos = event_handler.get_pos()

        if self.rect.collidepoint(pos):
            if event_handler.presses["left"]:
                self.was_held = True

            if event_handler.releases["left"] and self.was_held:
                self.on_click(*pos)
                self.is_clicked = True
                if callable(self.on_click_listener):
                    if self.click_pass_self:
                        self.on_click_listener(self.click_class, *pos, self)
                    else:
                        self.on_click_listener(self.click_class, *pos)
            elif event_handler.held["left"]:
                self.on_hold(*pos)
                self.is_held = True
                if callable(self.on_hold_listener):
                    if self.hold_pass_self:
                        self.on_hold_listener(self.hold_class, *pos, self)
                    else:
                        self.on_hold_listener(self.hold_class, *pos)

            self.on_hover(*pos)
            self.is_hovering = True
            if callable(self.on_hover_listener):
                if self.hover_pass_self:
                    self.on_hover_listener(self.hover_class, *pos, self)
                else:
                    self.on_hover_listener(self.hover_class, *pos)
        else:
            self.was_held = False

    def render(self) -> None:
        if self.img is None:
            self.render_non_image()
        else:
            self.render_image()

        self.label.render()

    def render_non_image(self) -> None:
        if self.color is None:
            return
        pygame.draw.rect(self.display, self.color.c, self.rect, width=0, border_radius=self.border_radius)
        if self.border_color:
            pygame.draw.rect(self.display, self.border_color.c, self.rect,
                             width=self.border_width, border_radius=self.border_radius)

    def render_image(self) -> None:
        self.display.blit(self.img, (self.rect.x, self.rect.y))

    def on_hover(self, x: int, y: int) -> None:
        pass

    def on_click(self, x: int, y: int) -> None:
        pass

    def on_hold(self, x: int, y: int) -> None:
        pass

    # Getters and Setters

    def set_on_hover_listener(self, listener: Callable, cls, pass_self: bool = False) -> Button:
        self.on_hover_listener = listener
        self.hover_class = cls
        self.hover_pass_self = pass_self
        return self

    def set_on_click_listener(self, listener: Callable, cls, pass_self: bool = False) -> Button:
        self.on_click_listener = listener
        self.click_class = cls
        self.click_pass_self = pass_self
        return self

    def set_on_hold_listener(self, listener: Callable, cls, pass_self: bool = False) -> Button:
        self.on_hold_listener = listener
        self.hold_class = cls
        self.hold_pass_self = pass_self
        return self

    def get_text(self) -> str:
        return self.label.text

