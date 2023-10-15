from abc import abstractmethod, ABC
from typing import Optional, Tuple, Any

import pygame

from bela.game.ui.label import Label


class Animation(ABC):

    def __init__(self, remove_on_finish: bool = False) -> None:
        self.finished = False
        self.just_finished = False
        self.remove_on_finish = remove_on_finish

    @abstractmethod
    def update(self) -> None:
        """Updates the animation."""

    @abstractmethod
    def get_current_data(self) -> Any:
        """Returns the current updated variables."""

    def is_finished(self) -> bool:
        return self.finished

    def is_just_finished(self) -> bool:
        return self.just_finished


class AnimationHandler:

    def __init__(self) -> None:
        self.animations = {}

    def update(self) -> None:
        to_remove = []

        for id_, animation in self.animations.items():
            if animation.remove_on_finish and animation.is_finished():
                to_remove.append(id_)
            else:
                animation.update()

        for id_ in to_remove:
            self.animations.pop(id_)

    def add_animation(self, animation: Animation, id_: str = None) -> None:
        self.animations[id_] = animation

    def remove_animation(self, id_: str) -> None:
        if not self.has(id_):
            return

        self.animations.pop(id_)

    def get_animation(self, id_: str) -> Optional[Animation]:
        return self.animations[id_]

    def has(self, id_: str) -> bool:
        return id_ in self.animations


class SimpleAnimation(Animation):

    def __init__(self, start_value: float, end_value: float, value_per_tick: float, remove_on_finish: bool = False) -> None:
        super().__init__(remove_on_finish)
        self.start_value = start_value
        self.end_value = end_value
        self.value_per_tick = value_per_tick
        self.remove_on_finish = remove_on_finish

    def update(self) -> None:
        self.just_finished = False

        if self.finished:
            return

        if self.value_per_tick < 0 and self.start_value <= self.end_value:
            self.just_finished = True
            self.finished = True
            return

        if self.value_per_tick > 0 and self.start_value >= self.end_value:
            self.just_finished = True
            self.finished = True
            return

        self.start_value += self.value_per_tick

    def get_current_data(self) -> Any:
        return self.start_value


class TextShootDownAnimation(Animation):

    def __init__(self, label1: Label, label2: Label, stop: int, y_vel: float, extra_labels: list[Label],
                 remove_on_finish: bool = False) -> None:
        super().__init__(remove_on_finish)
        self.label1 = label1
        self.label2 = label2
        self.stop = stop
        self.y_vel = y_vel
        self.extra_labels = extra_labels or []
        self.remove_on_finish = remove_on_finish

        self.label1_y = self.label1.get_pos()[1]
        self.label2_y = self.label2.get_pos()[1]

    def update(self) -> None:
        self.just_finished = False
        if self.finished:
            return
        if self.label1.get_pos()[1] >= self.stop:
            self.finished = True
            self.just_finished = True
            return
        if self.label2_y < self.label1_y:
            self.label2_y += self.y_vel
            self.label2.move(y=self.label2_y)
        if self.label2_y > self.label1_y - self.label1.get_size()[1] // 2:
            self.label1.move(y=int(self.label1.get_pos()[1] + self.y_vel))
            for label in self.extra_labels:
                label.move(y=int(label.get_pos()[1] + self.y_vel))

    def get_current_data(self) -> Any:
        return self.label1_y, self.label2_y


class FallingScreenAnimation(Animation):

    def __init__(self, size: Tuple[int, int], start_y: float, stop_y: float, velocity: float,
                 remove_on_finish: bool = False) -> None:
        super().__init__(remove_on_finish)
        self.w, self.h = size
        self.y = start_y
        self.stop_y = stop_y
        self.vel = velocity
        self.remove_on_finish = remove_on_finish

        self.g = 0.98
        self.acc = self.g

    def update(self) -> None:
        self.just_finished = False

        if self.finished:
            return

        self.vel += self.acc

        self.y += self.vel

        if self.y >= self.stop_y:
            self.y = self.stop_y

            self.finished = True
            self.just_finished = True

    def get_current_data(self) -> Any:
        return self.y


class SlidingScreenAnimation(Animation):

    def __init__(self, start: int, stop: int, direction: str, vel: float, remove_on_finish: bool = False) -> None:
        super().__init__(remove_on_finish)
        self.start = start
        self.stop = stop
        self.direction = direction
        self.remove_on_finish = remove_on_finish
        self.vel = []

        self.x = start
        self.y = start

        if self.direction == "up":
            self.vel = [0, -vel]
        elif self.direction == "down":
            self.vel = [0, vel]
        elif self.direction == "right":
            self.vel = [vel, 0]
        elif self.direction == "left":
            self.vel = [-vel, 0]
        else:
            raise ValueError(f"{self.direction} is an invalid direction.")

    def update(self) -> None:
        self.just_finished = False

        if self.finished:
            return

        self.x += self.vel[0]
        self.y += self.vel[1]

        if (
            self.x >= self.stop and self.direction == "right" or
            self.x <= self.stop and self.direction == "left" or
            self.y >= self.stop and self.direction == "down" or
            self.y <= self.stop and self.direction == "up"
        ):
            self.x = self.stop
            self.y = self.stop

            self.finished = True
            self.just_finished = True

    def get_current_data(self) -> Any:
        return int(self.x) if self.vel[0] else int(self.y)


class AnimationFactory:

    @staticmethod
    def create_simple_animation(start: float, end: float, value_per_tick: float, remove_on_finish: bool = False) -> SimpleAnimation:
        return SimpleAnimation(start, end, value_per_tick, remove_on_finish=remove_on_finish)

    @staticmethod
    def create_text_shoot_down_animation(label1: Label, label2: Label, stop: int, y_vel: float = 24,
                                         extra_labels: list[Label] = None, remove_on_finish: bool = False) -> Animation:
        return TextShootDownAnimation(label1, label2, stop, y_vel, extra_labels, remove_on_finish=remove_on_finish)

    @staticmethod
    def create_falling_screen_animation(size: Tuple[int, int], start_y: float = None, stop_y: float = 0,
                                        velocity: float = 10.0, remove_on_finish: bool = False) -> Animation:
        return FallingScreenAnimation(size, start_y if start_y is not None else -size[1], stop_y, velocity,
                                      remove_on_finish=remove_on_finish)

    @staticmethod
    def create_sliding_screen_animation(start: int, stop: int, direction: str, vel: float = 20,
                                        remove_on_finish: bool = False) -> Animation:
        return SlidingScreenAnimation(start, stop, direction, vel, remove_on_finish=remove_on_finish)


