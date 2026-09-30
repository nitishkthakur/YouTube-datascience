"""Fixture Scene 1: two beats, tiny animations. Used by render_all / assemble / pipeline tests."""

from manim import Circle, Create, Square

from dsanim import palette as P
from dsanim.scene import DSScene


class Scene01(DSScene):
    def construct(self):
        with self.beat("1.1"):
            self.play(Create(Circle(color=P.CONCEPT)), run_time=0.3)
        with self.beat("1.2"):
            self.play(Create(Square(color=P.PARAM)), run_time=0.3)
