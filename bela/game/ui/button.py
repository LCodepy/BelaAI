from __future__ import annotations

import time
from typing import Callable
import pygame

from bela.game.events.events import EventHandler
from bela.game.ui.label import Label
from bela.game.utils.assets import Assets
from bela.game.utils.colors import *


class Button:

    def __init__(self, display, center, size, font, center_x: bool = True, center_y: bool = True, text: str = None,
                 img: pygame.Surface = None, color: Color = Colors.dark_red,
                 font_color: Color = Colors.black, bold: bool = False, text_orientation: str = "center",
                 padding: int = 20) -> None:
        self.display = display
        self.x, self.y = center
        self.w, self.h = size
        self.text = text
        self.font = font
        self.img = img
        self.color = color
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

        self.last_hovered = False

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

        if self.last_hovered and not self.is_hovering:  # e.i. on_exit()
            self.color = self.color.darker(50)
        elif not self.last_hovered and self.is_hovering:  # e.i. on_enter()
            self.color = self.color.brighter(50)

        self.last_hovered = self.is_hovering

        self.is_clicked = False
        self.is_hovering = False
        self.is_held = False

        pos = event_handler.get_pos()

        if self.rect.collidepoint(pos):
            if event_handler.releases["left"]:
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

    def render(self) -> None:
        if self.img is None:
            self.render_non_image()
        else:
            self.render_image()

        self.label.render()

    def render_non_image(self) -> None:
        pygame.draw.rect(self.display, self.color.c, self.rect)

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

