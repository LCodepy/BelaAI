from typing import Tuple, Callable

import pygame

from bela.game.events.events import EventHandler
from bela.game.ui.label import Label
from bela.game.utils.assets import Assets
from bela.game.utils.colors import Color


class Button:

    def __init__(self, display, center, size, font, center_x: bool = True, center_y: bool = True, text: str = None,
                 img: pygame.Surface = None, color: Color = Color.red,
                 font_color: Tuple = (0, 0, 0), bold: bool = False, text_orientation: str = "center",
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

        self.is_hovering = False
        self.is_clicked = False
        self.is_held = False

    def set_text(self, text: str) -> None:
        self.text = text
        self.label.set_text(text)

    def update(self, event_handler: EventHandler) -> None:
        pos = event_handler.get_pos()
        if self.rect.collidepoint(pos):
            if event_handler.presses["left"]:
                self.on_click(*pos)
                self.is_clicked = True
                if callable(self.on_click_listener):
                    self.on_click_listener(*pos)
            elif event_handler.held["left"]:
                self.on_hold(*pos)
                self.is_held = False
                if callable(self.on_click_listener):
                    self.on_hold_listener(*pos)
            else:
                self.on_hover(*pos)
                self.is_hovering = False
                if callable(self.on_click_listener):
                    self.on_hover_listener(*pos)

    def render(self) -> None:
        if self.img is None:
            self.render_non_image()
        else:
            self.render_image()

        self.label.render()

    def render_non_image(self) -> None:
        pygame.draw.rect(self.display, self.color, self.rect)

    def render_image(self) -> None:
        self.display.blit(self.img, (self.rect.x, self.rect.y))

    def on_hover(self, x, y) -> None:
        pass

    def on_click(self, x, y) -> None:
        pass

    def on_hold(self, x, y) -> None:
        pass

    # Getters and Setters

    def set_on_hover_listener(self, listener: Callable[[int, int], None]) -> None:
        self.on_hover_listener = listener

    def set_on_click_listener(self, listener: Callable[[int, int], None]) -> None:
        self.on_click_listener = listener

    def set_on_hold_listener(self, listener: Callable[[int, int], None]) -> None:
        self.on_hold_listener = listener

