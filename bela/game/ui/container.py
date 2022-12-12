from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Optional

import pygame

from bela.game.events.events import EventHandler
from bela.game.ui.ui_object import UIObject
from bela.game.utils.colors import Color


@dataclass
class UIObjectWrapper:

    id: str
    object: UIObject
    pad_x: int
    pad_y: int
    fit_x: bool
    fit_y: bool


class Container(UIObject):

    def __init__(self, display: pygame.Surface, position: Tuple[int, int], size: Tuple[int, int], color: Color,
                 padding: int = 0, border_color: Color = None, border_radius: int = 0,
                 border_width: int = 0, center_x: bool = True, center_y: bool = True, active: bool = True) -> None:

        super().__init__(display, position, size, padding, border_color, border_radius, border_width)

        self.display = display
        self.x, self.y = position
        self.w, self.h = size
        self.color = color
        self.padding = padding
        self.border_color = border_color
        self.border_radius = border_radius
        self.border_width = border_width
        self.center_x = center_x
        self.center_y = center_y
        self.active = active

        self.surface = pygame.Surface((self.w, self.h), pygame.SRCALPHA)

        if not center_x:
            self.x += self.w // 2
        if not center_y:
            self.y += self.h // 2

        self.rect = pygame.Rect(self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)

        self.elements: list[UIObjectWrapper] = []
        self.current_y = 0

    def update_vars(self) -> None:
        self.surface = pygame.Surface((self.w, self.h), pygame.SRCALPHA)

        if not self.center_x:
            self.x += self.w // 2
        if not self.center_y:
            self.y += self.h // 2

        self.rect = pygame.Rect(self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)

        self.current_y = 0
        for element in self.elements:
            element.object.display = self.surface

            self.current_y += element.pad_y

            if element.fit_x:
                element.object.set_size((self.rect.w - element.pad_x * 2, element.object.get_size()[1]))
                element.object.update_vars()
            if element.fit_y:
                element.object.set_size((element.object.get_size()[0], (self.rect.h - self.current_y) - element.pad_y * 2))
                element.object.update_vars()

            element.object.move(self.w // 2, self.current_y, cy=False)
            element.object.update_vars()

            self.current_y += element.object.get_size()[1]
            self.current_y += element.pad_y

    def update(self, event_handler: EventHandler) -> None:
        for element in self.elements:
            element.object.update(event_handler.filtered(self.rect.x, self.rect.y))

    def render(self) -> None:
        pygame.draw.rect(self.surface, self.color.c, [0, 0, self.rect.w, self.rect.h], width=0,
                         border_radius=self.border_radius)
        if self.border_color:
            pygame.draw.rect(self.surface, self.border_color.c, [0, 0, self.rect.w, self.rect.h],
                             width=self.border_width, border_radius=self.border_radius)

        self.render_elements()

        self.display.blit(self.surface, (self.rect.x, self.rect.y))

    def render_elements(self) -> None:
        for element in self.elements:
            element.object.render()

    def add_element(self, element: UIObject, id_: str = None, pad_x: int = 0, pad_y: int = 0,
                    fit_x: bool = False, fit_y: bool = False, abs_x: int = None, abs_y: int = None) -> Container:
        if id_ is None:
            id_ = str(id(element))

        element.display = self.surface

        if abs_x or abs_y:  # if absolute position of the element is set
            element.move(abs_x or self.w // 2, abs_y or self.h // 2)
            element.update_vars()

            self.elements.append(
                UIObjectWrapper(id_, element, 0, 0, False, False)
            )
            return self

        # if relative position of the element is set

        self.current_y += pad_y

        if fit_x:
            element.set_size((self.rect.w - pad_x * 2, element.get_size()[1]))
            element.update_vars()
        if fit_y:
            element.set_size((element.get_size()[0], (self.rect.h - self.current_y) - pad_y * 2))
            element.update_vars()

        element.move(self.w // 2, self.current_y, cy=False)
        element.update_vars()

        self.elements.append(
            UIObjectWrapper(id_, element, pad_x, pad_y, fit_x, fit_y)
        )

        self.current_y += element.get_size()[1]
        self.current_y += pad_y

        return self

    def get_element(self, id_: str) -> Optional[UIObject]:
        for element in self.elements:
            if element.id == id_:
                return element.object

    def reset(self) -> None:
        self.elements.clear()
        self.current_y = 0

    def move(self, x: int = None, y: int = None, cx: bool = True, cy: bool = True) -> None:
        if x is not None:
            self.x = x
            if not cx:
                self.x += self.w // 2
        if y is not None:
            self.y = y
            if not cy:
                self.y += self.h // 2

        self.rect = pygame.Rect(self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)

    def get_size(self) -> Tuple[int, int]:
        return self.rect.size

    def get_center(self) -> Tuple[int, int]:
        return self.rect.center

    def set_size(self, size: Tuple[int, int]) -> None:
        self.w, self.h = size

    def set_display(self, surface: pygame.Surface) -> None:
        self.display = surface

