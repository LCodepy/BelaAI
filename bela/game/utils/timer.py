import time
from dataclasses import dataclass
from typing import Callable


@dataclass
class Timer:

    start: float
    duration: float
    activation: Callable
    cls: object


class TimerHandler:

    """
    Class for adding timers and countdowns.
    """

    timers: dict[str, Timer] = {}
    to_add: list[[str, Timer]] = []

    def update(self) -> None:
        for id_, timer in self.to_add:
            self.timers[id_] = timer

        to_remove = []
        for id_, timer in self.timers.items():
            if time.time() - timer.start >= timer.duration:
                timer.activation(timer.cls)
                to_remove.append(id_)

        for id_ in to_remove:
            self.timers.pop(id_)

    def add_timer(self, id_: str, duration: float, activation: Callable, cls: object) -> None:
        self.timers[id_] = Timer(time.time(), duration, activation, cls)

    def add_timer_during_exec(self, id_: str, duration: float, activation: Callable, cls: object) -> None:
        self.to_add.append([id_, Timer(time.time(), duration, activation, cls)])

    def remove_timer(self, id_: str) -> None:
        self.timers.pop(id_)


