"""Scatter — a cloud of data points that remembers its data, so scenes can collapse it onto an
axis, restore it, and highlight the points inside a band.
"""

from __future__ import annotations

import numpy as np
from manim import Dot, VGroup

from dsanim import palette as P

DOT_RADIUS = 0.035  # ~4.7 px at 1080p: 400 points stay distinguishable without clumping


class Scatter(VGroup):
    def __init__(self, axes, x, y, color: str = P.DATA, radius: float = DOT_RADIUS):
        super().__init__()
        self.axes = axes
        self.xs = np.asarray(x, dtype=float)
        self.ys = np.asarray(y, dtype=float)
        if self.xs.shape != self.ys.shape:
            raise ValueError("x and y must have the same length")
        self.base_color = color
        self.add(*[Dot(axes.c2p(a, b), radius=radius, color=color) for a, b in zip(self.xs, self.ys)])

    def positions(self) -> np.ndarray:
        """Scene positions of each point at its (x, y)."""
        return np.array([self.axes.c2p(a, b) for a, b in zip(self.xs, self.ys)])

    def collapsed(self, x_value: float) -> "Scatter":
        """A copy with every point moved to x = x_value (same y): 'ignore x'."""
        copy = self.copy()
        for dot, b in zip(copy, self.ys):
            dot.move_to(self.axes.c2p(x_value, b))
        return copy

    def focus_band(self, x0: float, half_width: float, focus_color: str = P.DATA_FOCUS,
                   rest_opacity: float = P.FADED_OPACITY) -> "Scatter":
        """Colour points inside |x - x0| < half_width with focus_color; fade the rest.

        Mutates in place (cheap enough to call from an updater during a sweep).
        """
        inside = np.abs(self.xs - x0) < half_width
        for dot, keep in zip(self, inside):
            if keep:
                dot.set_fill(focus_color, opacity=1.0)
            else:
                dot.set_fill(self.base_color, opacity=rest_opacity)
        return self

    def unfocus(self) -> "Scatter":
        for dot in self:
            dot.set_fill(self.base_color, opacity=1.0)
        return self
