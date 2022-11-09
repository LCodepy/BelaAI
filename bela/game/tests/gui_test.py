import pygame

from bela.game.events.events import EventHandler
from bela.game.ui.label import Label
from bela.game.utils.colors import Colors


win = pygame.display.set_mode((800, 600), pygame.SRCALPHA)
pygame.display.set_caption("GUI testing")
clock = pygame.time.Clock()

event_handler = EventHandler()


class Faller:

    def __init__(self) -> None:
        self.color = (0, 200, 20)
        self.w, self.h = win.get_size()

        self.y = -self.h
        self.vel = 10
        self.g = 9.8 * 10**-1
        self.acc = self.g

        self.surf = pygame.Surface(win.get_size())

    def update(self) -> None:
        self.just_finished = False

        if self.finished:
            return

        self.vel += self.acc

        self.y += self.vel

        if self.y >= self.h:
            self.y = self.h

            self.vel = -self.vel * 0.5

            if abs(self.vel) < self.acc and self.y == self.h:
                self.finished = True
                self.just_finished = True

    def render(self) -> None:
        self.surf.fill(self.color)
        win.blit(self.surf, (0, self.y - self.h))


faller = Faller()


running = True
while running:

    faller.update()

    win.fill((0, 0, 20))

    # rendering
    faller.render()

    pygame.display.update()
    clock.tick(60)

    if not event_handler.loop():
        break

pygame.quit()
