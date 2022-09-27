import pygame

from bela.game.events.events import EventHandler
from bela.game.ui.label import Label
from bela.game.utils.colors import Colors


win = pygame.display.set_mode((800, 600), pygame.SRCALPHA)
pygame.display.set_caption("GUI testing")
clock = pygame.time.Clock()

event_handler = EventHandler()


class L1:

    def __init__(self) -> None:
        self.label_x, self.label_y = win.get_width() // 2, -100
        self.y_acc = 0.001
        self.y_vel = 0

        self.label = Label(win, (self.label_x, self.label_y), (300, 100), pygame.font.SysFont("Arial", 60),
                           text="BELOT", font_color=Colors.white)

    def update(self) -> None:
        if self.label_y >= 200:
            self.y_vel = -self.y_vel
            self.y_acc *= 2

        if self.y_acc >= 0.05:
            self.y_acc = 0
            self.y_vel = 0

        self.y_vel = min(self.y_vel + self.y_acc, 3)
        self.label_y += self.y_vel

        self.label.move(y=self.label_y)

    def render(self) -> None:
        self.label.render()


class L2:

    def __init__(self) -> None:
        self.label1_x, self.label1_y = win.get_width() // 2, 300
        self.label2_x, self.label2_y = win.get_width() // 2, -200

        self.label1 = Label(win, (self.label1_x, self.label1_y), (300, 100), pygame.font.SysFont("Arial", 60),
                            text="BELOT", font_color=Colors.white)
        self.label2 = Label(win, (self.label2_x, self.label2_y), (500, 100), pygame.font.SysFont("Arial", 60),
                            text="MATCH OVER", font_color=Colors.white)

        self.stop = 800
        self.y_vel = 22

    def update(self) -> bool:
        if self.label1_y >= self.stop:
            return False
        if self.label2_y < self.label1_y:
            self.label2_y += self.y_vel
            self.label2.move(y=self.label2_y)
        if self.label2_y > self.label1_y - self.label1.get_size()[1] // 2:
            self.label1.move(y=int(self.label1.get_pos()[1] + self.y_vel))
        return True

    def render(self) -> None:
        self.label1.render()
        self.label2.render()


label = L2()


running = True
while running:

    label.update()

    win.fill((0, 0, 20))

    # rendering

    label.render()

    pygame.display.update()
    clock.tick(60)

    if not event_handler.loop():
        break

pygame.quit()
