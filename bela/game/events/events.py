from collections import defaultdict
from typing import Union

import pygame


class EventHandler:

    def __init__(self):
        self.keys = defaultdict(lambda: False)
        self.unicode_keys = defaultdict(lambda: False)

        self.presses = {"left": False, "middle": False, "right": False, "up": False, "down": False}
        self.releases = {"left": False, "middle": False, "right": False, "up": False, "down": False}
        self.held = {"left": False, "middle": False, "right": False}
        self.scrolls = {"up": False, "down": False}

    def loop(self):
        self.reset()

        if pygame.mouse.get_pressed()[0]:
            self.held["left"] = True
        if pygame.mouse.get_pressed()[1]:
            self.held["middle"] = True
        if pygame.mouse.get_pressed()[2]:
            self.held["right"] = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.KEYDOWN:
                self.keys[event.key] = True
                self.unicode_keys[event.unicode] = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button < 4:
                    i = event.button - 1
                    self.presses[list(self.presses.keys())[i]] = True
                elif event.button == 4:
                    self.scrolls["up"] = True
                else:
                    self.scrolls["down"] = True

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button < 4:
                    i = event.button - 1
                    self.releases[list(self.releases.keys())[i]] = True

        return True

    def reset(self):
        self.keys = defaultdict(lambda: False)
        self.unicode_keys = defaultdict(lambda: False)

        self.presses = {"left": False, "middle": False, "right": False, "up": False, "down": False}
        self.releases = {"left": False, "middle": False, "right": False, "up": False, "down": False}
        self.held = {"left": False, "middle": False, "right": False}
        self.scrolls = {"up": False, "down": False}

    def is_key_pressed(self, key: int) -> bool:
        return pygame.key.get_pressed()[key]

    def key_just_pressed(self, key: Union[int, str]) -> bool:
        if isinstance(key, str):
            return self.unicode_keys[key]
        return self.keys[key]

    def get_pos(self):
        return pygame.mouse.get_pos()
