import pygame


class EventHandler:

    def __init__(self):
        self.key = None
        self.current_key = None
        self.key_unicode = None

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
                self.key = self.current_key = event.key
                self.key_unicode = event.unicode

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
        self.key = None
        self.key_unicode = None

        self.presses = {"left": False, "middle": False, "right": False, "up": False, "down": False}
        self.releases = {"left": False, "middle": False, "right": False, "up": False, "down": False}
        self.held = {"left": False, "middle": False, "right": False}
        self.scrolls = {"up": False, "down": False}

    def get_pos(self):
        return pygame.mouse.get_pos()
