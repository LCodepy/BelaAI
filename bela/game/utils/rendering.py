from typing import Tuple

import pygame


def render_outline(img: pygame.Surface, surface: pygame.Surface, color: Tuple[int, int, int, int], x: int, y: int, xo: int, yo: int, xyo: int) -> None:
    mask = pygame.mask.from_surface(img).to_surface()
    mask.set_colorkey((0, 0, 0))
    img = pygame.Surface(mask.get_size(), pygame.SRCALPHA)
    img.fill(color)
    mask.set_colorkey((255, 255, 255))
    img.blit(mask, (0, 0))
    img.set_colorkey((0, 0, 0))

    for j in range(-xo, xo+1):
        if j == 0: continue
        surface.blit(img, (x - img.get_width() // 2 + j, y - img.get_height() // 2))
    for j in range(-yo, yo+1):
        if j == 0: continue
        surface.blit(img, (x - img.get_width() // 2, y - img.get_height() // 2 + j))
    for j in range(-xyo, xyo+1):
        if j == 0: continue
        surface.blit(img, (x - img.get_width() // 2 + j, y - img.get_height() // 2 + j,))


