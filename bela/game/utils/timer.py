import time
from typing import Callable


class Timer:

    """
    Class for adding timers and countdowns.
    """

    timers = []

    def update(self) -> None:
        for timer in self.timers:
            if time.time() - timer[0] >= timer[1]:
                timer[2]()

    def add_timer(self, duration: float, activation: Callable) -> None:
        self.timers.append([time.time(), duration, activation])


