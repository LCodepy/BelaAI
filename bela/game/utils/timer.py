import time
from dataclasses import dataclass
from typing import Callable


@dataclass
class Timer:

    start: float
    duration: float
    activation: Callable


class TimerHandler:

    """
    Class for adding timers and countdowns.
    """

    timers: dict[str, Timer] = {}

    def update(self) -> None:
        for id_, timer in self.timers.items():
            if time.time() - timer.start >= timer.duration:
                timer.activation()
                self.timers.pop(id_)

    def add_timer(self, id_: str, duration: float, activation: Callable) -> None:
        self.timers[id_] = Timer(time.time(), duration, activation)


