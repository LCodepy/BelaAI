from os.path import join

import pygame

from bela.game.utils.singleton import Singleton


class Assets(metaclass=Singleton):

    PATH_IMAGES = "Assets/Images/"

    def __init__(self) -> None:
        self.font18 = pygame.font.SysFont("consolas", 18)
        self.font24 = pygame.font.SysFont("consolas", 24)
        self.font32 = pygame.font.SysFont("consolas", 32)
        self.font48 = pygame.font.SysFont("consolas", 48)
        self.font64 = pygame.font.SysFont("consolas", 64)


