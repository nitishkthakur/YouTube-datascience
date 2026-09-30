"""Fixture Scene 2: one beat with a mark."""

from manim import Dot, FadeIn

from dsanim import palette as P
from dsanim.scene import DSScene


class Scene02(DSScene):
    def construct(self):
        with self.beat("2.1") as b:
            b.wait_until("a")
            self.play(FadeIn(Dot(color=P.MODEL)), run_time=0.2)
