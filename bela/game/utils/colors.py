from __future__ import annotations

from typing import Tuple


class Color:

    def __init__(self, r: int, g: int, b: int, alpha: int = 255) -> None:
        self.r = r
        self.g = g
        self.b = b
        self.alpha = alpha

    # Functions

    @property
    def c(self) -> Tuple[int, int, int, int]:
        return min(255, max(self.r, 0)), min(255, max(self.g, 0)), min(255, max(self.b, 0)), min(255, max(self.alpha, 0))

    def brighter(self, value: int) -> Color:
        return Color(self.r + value, self.g + value, self.b + value, self.alpha)

    def darker(self, value: int) -> Color:
        return Color(self.r - value, self.g - value, self.b - value, self.alpha)

    @staticmethod
    def color(color) -> Color:
        if len(color) == 3:
            return Color(color[0], color[1], color[2])
        return Color(color[0], color[1], color[2], color[3])


class Colors:

    white = Color(255, 255, 255)
    black = Color(0, 0, 0)
    red = Color(255, 0, 0)
    dark_red = Color(205, 0, 0)
    green = Color(0, 255, 0)
    blue = Color(0, 0, 255)
    yellow = Color(255, 255, 0)
    brown = Color(100, 60, 20)
    dark_grey = Color(50, 50, 50)
    grey = Color(100, 100, 100)
    light_grey = Color(200, 200, 200)
