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
        self.font14 = pygame.font.SysFont("consolas", 14)
        self.font18 = pygame.font.SysFont("consolas", 18)
        self.font24 = pygame.font.SysFont("consolas", 24)
        self.font32 = pygame.font.SysFont("consolas", 32)
        self.font48 = pygame.font.SysFont("consolas", 48)
        self.font64 = pygame.font.SysFont("consolas", 64)

        self.card_names = [
            list(map(lambda x: (x, "herc"), ["7", "8", "9", "cener", "unter", "baba", "kralj", "kec"])),
            list(map(lambda x: (x, "karo"), ["7", "8", "9", "cener", "unter", "baba", "kralj", "kec"])),
            list(map(lambda x: (x, "pik"), ["7", "8", "9", "cener", "unter", "baba", "kralj", "kec"])),
            list(map(lambda x: (x, "tref"), ["7", "8", "9", "cener", "unter", "baba", "kralj", "kec"]))
        ]
        self.card_mappings = [
            *([0]*8), *([1]*8), *([2]*8), 4, *([3]*8)
        ]

        self.card_spritesheet = self.load_sprite_sheet("karte_spritesheet.png", 11, 3, self.card_mappings, 0.5 * 0.365)[:-1]
        self.card_images = self.edit_sprite_sheet(self.card_spritesheet, self.card_names)
        self.card_back = pygame.image.load(self.PATH_IMAGES + "karta_okrenuta.png").convert_alpha()
        self.card_back = pygame.transform.scale(self.card_back, (self.card_back.get_width() * 0.5 * 0.365, self.card_back.get_height() * 0.5 * 0.365))
        self.card_width, self.card_height = self.card_images[("kec", "herc")].get_size()

        self.symbols = {
            "tref": pygame.image.load(self.PATH_IMAGES + "tref.png").convert_alpha(),
            "herc": pygame.image.load(self.PATH_IMAGES + "herc.png").convert_alpha(),
            "karo": pygame.image.load(self.PATH_IMAGES + "karo.png").convert_alpha(),
            "pik": pygame.image.load(self.PATH_IMAGES + "pik.png").convert_alpha(),
        }

        self.table = pygame.image.load(self.PATH_IMAGES + "stol.png")

        self.arrow_back = pygame.image.load(self.PATH_IMAGES + "arrow_back.png")

    def load_sprite_sheet(self, filename: str, rows: int, cols: int, mappings: list[int], size: float = 1) -> list[list[pygame.Surface]]:
        sheet = [[] for _ in range(len(set(mappings)))]

        img = pygame.image.load(self.PATH_IMAGES + filename).convert_alpha()
        #img = pygame.transform.scale(img, (int(img.get_width() * size), int(img.get_height() * size)))

        for y, i in enumerate(range(0, img.get_height(), img.get_height() // rows)):
            for x, j in enumerate(range(0, img.get_width(), img.get_width() // cols)):
                if j + img.get_width() // cols > img.get_width() or i + img.get_height() // rows > img.get_height():
                    continue
                mapping = mappings[y * cols + x]
                subsurf_img = img.subsurface([j, i, img.get_width() // cols, img.get_height() // rows])
                subsurf_img = pygame.transform.scale(subsurf_img, (int(subsurf_img.get_width() * size), int(subsurf_img.get_height() * size)))
                sheet[mapping].append(subsurf_img)

        return sheet

    def edit_sprite_sheet(self, sheet: list[list[pygame.Surface]], names: list[list]) -> dict[Tuple[str, str], pygame.Surface]:
        d = {}
        for i in range(len(sheet)):
            for j in range(len(sheet[0])):
                d[names[i][j]] = sheet[i][j]
        return d

