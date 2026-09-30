"""Fixture scenes for beat-timing regression tests."""

from manim import Circle, Create, FadeIn, Square, ValueTracker

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


class ExtendsBeat(DSScene):
    """2 s of animation in beat 1.1 with 1.5 s of silent visual time allowed."""

    def construct(self):
        with self.beat("1.1", extend=1.5):
            self.play(Create(Circle(color=P.CONCEPT)), run_time=2.0)


class ExtendTooSmall(DSScene):
    """2 s of animation in beat 1.1 with only 0.5 s of silent visual time allowed."""

    def construct(self):
        with self.beat("1.1", extend=0.5):
            self.play(Create(Circle(color=P.CONCEPT)), run_time=2.0)


class LeavesSafeArea(DSScene):
    """Ends beat 1.1 with a square centred on the safe area's right edge (half outside)."""

    def construct(self):
        with self.beat("1.1"):
            self.add(Square(color=P.ERROR).move_to([self.layout.safe.right, 0, 0]))


class StaysInSafeArea(DSScene):
    """Ends beat 1.1 with a square in the middle, plus invisible things 'off-screen'."""

    def construct(self):
        with self.beat("1.1"):
            self.add(Square(color=P.CONCEPT), ValueTracker(2200))
            self.add(Square(stroke_opacity=0, fill_opacity=0).move_to([100, 0, 0]))
