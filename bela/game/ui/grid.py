from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Optional, Union

import pygame

from bela.game.events.events import EventHandler
from bela.game.ui.ui_object import UIObject
from bela.game.utils.colors import Colors, Color


@dataclass
class GridCell:

    grid_pos: Tuple[int, int]
    size: Tuple[int, int]
    object: Optional[UIObject]
    pad_x: int
    pad_y: int


class Grid(UIObject):

    def __init__(self, display: pygame.Surface, position: Tuple[int, int],
                 size: Tuple[Union[int, str], Union[int, str]], grid_size: Tuple[int, int], padding: int = 0,
                 center_x: bool = True, center_y: bool = True, render_row_splitter: bool = False,
                 render_col_splitter: bool = False, cell_splitter_color: Color = Colors.white) -> None:
        super().__init__(display, position, size, padding)

        self.display = display
        self.x, self.y = position
        self.w, self.h = size
        self.padding = padding
        self.center_x = center_x
        self.center_y = center_y
        self.grid_size = grid_size
        self.render_row_splitter = render_row_splitter
        self.render_col_splitter = render_col_splitter
        self.cell_splitter_color = cell_splitter_color

        if self.w == "fit":
            self.w = 0
        if self.h == "fit":
            self.h = 0

        if not center_x:
            self.x += self.w // 2
        if not center_y:
            self.y += self.h // 2

        self.rect = pygame.Rect(self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)

        self.grid = self.create_grid()

    def create_grid(self) -> list[GridCell]:
        grid = []
        for i in range(self.grid_size[0]):
            for j in range(self.grid_size[1]):
                w = self.rect.w // self.grid_size[1]
                h = self.rect.h // self.grid_size[0]
                grid.append(GridCell((i, j), (w, h), None, 0, 0))
        return grid

    def update(self, event_handler: EventHandler) -> None:
        for cell in self.grid:
            if cell.object:
                cell.object.update(event_handler)

    def render(self) -> None:
        for cell in self.grid:
            if cell.object:
                cell.object.render()

        if self.render_row_splitter:
            for i in range(1, self.grid_size[0]):
                pygame.draw.line(self.display, self.cell_splitter_color.c,
                                 (self.rect.x, self.rect.y + i * self.rect.h // self.grid_size[0]),
                                 (self.rect.x + self.rect.w, self.rect.y + i * self.rect.h // self.grid_size[0]))

        if self.render_col_splitter:
            for j in range(1, self.grid_size[1]):
                pygame.draw.line(self.display, self.cell_splitter_color.c,
                                 (self.rect.x + j * self.rect.w // self.grid_size[1], self.rect.y),
                                 (self.rect.x + j * self.rect.w // self.grid_size[1], self.rect.y + self.rect.h))

    def add_element(self, element: UIObject, row: int, col: int, pad_x: int = 0, pad_y: int = 0) -> Grid:
        for cell in self.grid:
            if cell.grid_pos == (row, col):
                cell.object = element
                cell.pad_x = pad_x
                cell.pad_y = pad_y

                cell.object.set_display(self.display)
                x = self.rect.x + int(self.rect.w // self.grid_size[1] * (cell.grid_pos[1] + 0.5))
                y = self.rect.y + int(self.rect.h // self.grid_size[0] * (cell.grid_pos[0] + 0.5))
                cell.object.move(x, y)
                cell.object.update_vars()
                break

        return self

    def update_vars(self) -> None:
        if not self.center_x:
            self.x += self.w // 2
        if not self.center_y:
            self.y += self.h // 2

        self.rect = pygame.Rect(self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)

        for cell in self.grid:
            cell.size = (self.rect.w // self.grid_size[0], self.rect.h // self.grid_size[1])
            if cell.object:
                cell.object.set_display(self.display)
                x = self.rect.x + int(self.rect.w // self.grid_size[1] * (cell.grid_pos[1] + 0.5))
                y = self.rect.y + int(self.rect.h // self.grid_size[0] * (cell.grid_pos[0] + 0.5))
                cell.object.move(x, y)
                cell.object.update_vars()

    def move(self, x: int = None, y: int = None, cx: bool = True, cy: bool = True) -> None:
        if x is not None:
            self.x = x
            if not cx:
                self.x += self.w // 2
        if y is not None:
            self.y = y
            if not cy:
                self.y += self.h // 2

        last_x = self.rect.x
        last_y = self.rect.y

        self.rect.x = self.x
        self.rect.y = self.y

        x_dist = self.rect.x - last_x
        y_dist = self.rect.y - last_y

        for cell in self.grid:
            cell.size = (self.rect.w // self.grid_size[0], self.rect.h // self.grid_size[1])
            if cell.object:
                x, y = cell.object.get_center()
                cell.object.move(x + x_dist, y + y_dist)
                cell.object.update_vars()

    def get_cell_element(self, grid_pos: Tuple[int, int]) -> None:
        for cell in self.grid:
            if cell.grid_pos == grid_pos:
                return cell.object

    def get_size(self) -> Tuple[int, int]:
        return self.rect.size

    def get_center(self) -> Tuple[int, int]:
        return self.rect.center

    def set_size(self, size: Tuple[int, int]) -> None:
        self.w, self.h = size

    def set_display(self, surface: pygame.Surface) -> None:
        self.display = surface
