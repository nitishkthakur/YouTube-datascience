"""GaussianSlice — a Normal density drawn on its side along a vertical line of an Axes.

Used for the marginal distribution of y (baseline on the y-axis) and for conditional
distributions of y given x (baseline at the band's x). The density bulges horizontally;
its vertical position and spread are in the axes' y units, so mu and sigma read directly
off the y-axis.

Height convention: every slice is drawn with the same `peak_width` (shape, not density):
sigma varies ~7x across a conditional sweep, so true densities would range from a sliver to
a spike. Slices therefore compare location and spread, not height. Pass a peak_width that
scales with 1/sigma if a scene needs density-comparable slices.
"""

from __future__ import annotations

import numpy as np
from manim import AnimationGroup, Create, DashedLine, FadeIn, Line, VGroup, VMobject

from dsanim import palette as P

INFLECTION = float(np.exp(-0.5))  # density at mu +- sigma, relative to the peak


class GaussianSlice(VGroup):
    """Normal(mu, sigma^2) density along the vertical line x = x0 of `axes`.

    side = +1 bulges right, -1 bulges left. `span` = how many sigmas each way to draw; the
    curve is clipped to the axes' y-range.
    """

    def __init__(self, axes, x0: float, mu: float, sigma: float, peak_width: float = 1.2,
                 side: int = 1, span: float = 3.5, color: str = P.CONCEPT,
                 fill_opacity: float = 0.25, stroke_width: float = 4, samples: int = 121):
        super().__init__()
        if sigma <= 0:
            raise ValueError("sigma must be > 0")
        if side not in (1, -1):
            raise ValueError("side must be +1 or -1")
        self.axes, self.x0, self.mu, self.sigma = axes, x0, mu, sigma
        self.peak_width, self.side, self.span, self.samples = peak_width, side, span, samples
        self.fill = VMobject(stroke_width=0, fill_color=color, fill_opacity=fill_opacity)
        self.curve = VMobject(stroke_color=color, stroke_width=stroke_width)
        self.add(self.fill, self.curve)
        self._rebuild()

    def _rebuild(self) -> None:
        y_min, y_max = self.axes.y_range[0], self.axes.y_range[1]
        lo = max(self.mu - self.span * self.sigma, y_min)
        hi = min(self.mu + self.span * self.sigma, y_max)
        ys = np.linspace(lo, hi, self.samples)
        self.curve_points = np.array([self._point(y) for y in ys])
        base_lo, base_hi = self.base_point(lo), self.base_point(hi)
        self.fill.set_points_as_corners([base_lo, *self.curve_points, base_hi, base_lo])
        self.curve.set_points_smoothly(self.curve_points)

    def set_params(self, x0: float | None = None, mu: float | None = None,
                   sigma: float | None = None) -> "GaussianSlice":
        """Move/reshape in place (cheaper than rebuilding; keeps mean_line() etc. valid).
        Use from an updater during a sweep."""
        if x0 is not None:
            self.x0 = x0
        if mu is not None:
            self.mu = mu
        if sigma is not None:
            if sigma <= 0:
                raise ValueError("sigma must be > 0")
            self.sigma = sigma
        self._rebuild()
        return self

    def appear(self, run_time: float = P.RUN_TIME) -> AnimationGroup:
        """Draw the curve and fade the fill, as one animation of the whole slice."""
        return AnimationGroup(Create(self.curve), FadeIn(self.fill), run_time=run_time)

    # --- geometry -----------------------------------------------------------------------
    def base_point(self, y: float) -> np.ndarray:
        """Point on the baseline (x = x0) at data height y."""
        return self.axes.c2p(self.x0, y)

    def width_at(self, y: float) -> float:
        """Horizontal extent of the bulge at data height y, in scene units."""
        return self.peak_width * float(np.exp(-0.5 * ((y - self.mu) / self.sigma) ** 2))

    def _point(self, y: float) -> np.ndarray:
        return self.base_point(y) + np.array([self.side * self.width_at(y), 0.0, 0.0])

    def peak_point(self) -> np.ndarray:
        return self._point(self.mu)

    # --- annotations ------------------------------------------------------------------------
    def mean_line(self, color: str = P.CONCEPT, stroke_width: float = 3) -> Line:
        """Horizontal line from the baseline to the peak at y = mu (label it 'mu')."""
        return Line(self.base_point(self.mu), self.peak_point(), color=color,
                    stroke_width=stroke_width)

    def sigma_segment(self, color: str = P.CONCEPT, stroke_width: float = 3) -> DashedLine:
        """Vertical segment from mu to mu + sigma at the inflection-point width (label 'sigma').

        The curve's inflection points sit at mu +- sigma, where the density is exp(-1/2) of
        its peak — so this segment ends exactly on the curve.
        """
        dx = np.array([self.side * self.peak_width * INFLECTION, 0.0, 0.0])
        return DashedLine(self.base_point(self.mu) + dx, self.base_point(self.mu + self.sigma) + dx,
                          color=color, stroke_width=stroke_width)
