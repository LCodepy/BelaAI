import os.path
from os.path import join
from typing import Tuple

import pygame

from bela.game.utils.singleton import Singleton


class Assets(metaclass=Singleton):

    """
    Class for loading and accessing all assets in the project.
    """

    PATH_IMAGES = "Assets/Images/"

    def __init__(self) -> None:
        self.font18 = pygame.font.SysFont("consolas", 18)
        self.font24 = pygame.font.SysFont("consolas", 24)
        self.font32 = pygame.font.SysFont("consolas", 32)
        self.font48 = pygame.font.SysFont("consolas", 48)
        self.font64 = pygame.font.SysFont("consolas", 64)

        self.card_names = [
            list(map(lambda x: (x, "herc"), ["kec", "7", "8", "9", "cener", "unter", "baba", "kralj"])),
            list(map(lambda x: (x, "pik"), ["kec", "7", "8", "9", "cener", "unter", "baba", "kralj"])),
            list(map(lambda x: (x, "karo"), ["kec", "7", "8", "9", "cener", "unter", "baba", "kralj"])),
            list(map(lambda x: (x, "tref"), ["kec", "7", "8", "9", "cener", "unter", "baba", "kralj"]))
        ]
        self.card_images = self.edit_sprite_sheet(self.load_sprite_sheet("karte.png", 4, 8, 0.5), self.card_names)
        self.card_back = pygame.image.load(self.PATH_IMAGES + "karta_odiza.png").convert_alpha()
        self.card_back = pygame.transform.scale(self.card_back, (self.card_back.get_width() // 2, self.card_back.get_height() // 2))
        self.card_width, self.card_height = self.card_images[("kec", "herc")].get_size()

        self.table = pygame.image.load(self.PATH_IMAGES + "stol.png")

    def load_sprite_sheet(self, filename: str, rows: int, cols: int, size: float = 1) -> list[list[pygame.Surface]]:
        sheet = []

        img = pygame.image.load(self.PATH_IMAGES + filename).convert_alpha()
        img = pygame.transform.scale(img, (int(img.get_width() * size), int(img.get_height() * size)))

        for x, i in enumerate(range(0, img.get_height(), img.get_height() // rows)):
            sheet.append([])
            for j in range(0, img.get_width(), img.get_width() // cols):
                sheet[x].append(img.subsurface([j, i, img.get_width() // cols, img.get_height() // rows]))

        return sheet

    def edit_sprite_sheet(self, sheet: list[list[pygame.Surface]], names: list[list]) -> dict[Tuple[str, str], pygame.Surface]:
        d = {}
        for i in range(len(sheet)):
            for j in range(len(sheet[0])):
                d[names[i][j]] = sheet[i][j]
        return d

