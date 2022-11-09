from abc import abstractmethod, ABC
from typing import Optional, Tuple, Any

import pygame

from bela.game.ui.label import Label


class Animation(ABC):

    def __init__(self) -> None:
        self.finished = False
        self.just_finished = False

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
        self.animations = []

    def update(self) -> None:
        for i, animation in enumerate(self.animations):
            animation[1].update()

    def add_animation(self, animation: Animation, id_: str = None) -> None:
        self.animations.append([id_, animation])

    def remove_animation(self, id_: str) -> None:
        if not self.has(id_):
            return
        idx = 0
        for i, animation in enumerate(self.animations):
            if animation[0] == id_:
                idx = i
        self.animations.pop(idx)

    def get_animation(self, id_: str) -> Optional[Animation]:
        for animation in self.animations:
            if animation[0] == id_:
                return animation[1]
        return

    def has(self, id_: str) -> bool:
        return any(animation[0] == id_ for animation in self.animations)


class TextShootDownAnimation(Animation):

    def __init__(self, label1: Label, label2: Label, stop: int, y_vel: float, extra_labels: list[Label]) -> None:
        super().__init__()
        self.label1 = label1
        self.label2 = label2
        self.stop = stop
        self.y_vel = y_vel
        self.extra_labels = extra_labels or []

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

    def __init__(self, size: Tuple[int, int], start_y: float, stop_y: float, velocity: float) -> None:
        super().__init__()
        self.w, self.h = size
        self.y = start_y
        self.stop_y = stop_y
        self.vel = velocity

        self.g = 9.8 * 10**-1
        self.acc = self.g

    def update(self) -> None:
        self.just_finished = False

        if self.finished:
            return

        self.vel += self.acc

        self.y += self.vel

        if self.y >= self.stop_y:
            self.y = self.stop_y

            self.vel = -self.vel * 0.5

            if abs(self.vel) < self.acc and self.y == self.stop_y:
                self.finished = True
                self.just_finished = True

    def get_current_data(self) -> Any:
        return self.y


class AnimationFactory:

    @staticmethod
    def create_text_shoot_down_animation(label1: Label, label2: Label, stop: int, y_vel: float = 24,
                                         extra_labels: list[Label] = None) -> Animation:
        return TextShootDownAnimation(label1, label2, stop, y_vel, extra_labels)

    @staticmethod
    def create_falling_screen_animation(size: Tuple[int, int], start_y: float = None, stop_y: float = 0,
                                        velocity: float = 10.0) -> Animation:
        return FallingScreenAnimation(size, start_y if start_y is not None else -size[1], stop_y, velocity)



