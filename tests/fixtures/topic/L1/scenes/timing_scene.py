"""Fixture scenes for beat-timing regression tests."""

from manim import Circle, Create, FadeIn

from dsanim import palette as P
from dsanim.scene import DSScene


class FitsBeat(DSScene):
    """0.5 s of animation inside beat 1.1."""

    def construct(self):
        with self.beat("1.1"):
            self.play(Create(Circle(color=P.CONCEPT)), run_time=0.5)


class OverrunsBeat(DSScene):
    """3 s of animation inside beat 1.1 — must raise NarrationOverrun if audio is shorter."""

    def construct(self):
        with self.beat("1.1"):
            self.play(FadeIn(Circle(color=P.ERROR)), run_time=3.0)


class WaitsForMark(DSScene):
    """Waits until [[go]] then animates briefly."""

    def construct(self):
        with self.beat("1.1") as b:
            b.wait_until("go")
            self.play(Create(Circle(color=P.CONCEPT)), run_time=0.2)
