import pygame

from bela.game.events.events import EventHandler
from bela.game.ui.label import Label
from bela.game.utils.colors import Colors


win = pygame.display.set_mode((800, 600), pygame.SRCALPHA)
pygame.display.set_caption("GUI testing")
clock = pygame.time.Clock()

event_handler = EventHandler()

label_x, label_y = win.get_width() // 2, -100
y_acc = 0.001
y_vel = 0

label = Label(win, (label_x, label_y), (300, 100), pygame.font.SysFont("Arial", 60), text="BELOT", font_color=Colors.white)

running = True
while running:

    if label_y >= 400:
        y_vel = -y_vel
        y_acc *= 2

    if y_acc >= 0.05:
        y_acc = 0
        y_vel = 0

    y_vel = min(y_vel + y_acc, 3)
    label_y += y_vel

    label.move(y=label_y)

    win.fill((0, 0, 20))

    # rendering

    label.render()

    pygame.display.update()
    clock.tick()

    if not event_handler.loop():
        break

pygame.quit()
