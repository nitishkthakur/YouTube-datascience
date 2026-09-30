"""Conditioning mechanics: the band at X = x, the conditional slice inside it, and the mean
trace left behind as the band sweeps — which is the regression function E[Y | X = x].
"""

from __future__ import annotations

from manim import Rectangle

from dsanim import palette as P, stats
from dsanim.components.gaussian import GaussianSlice


def band(axes, x0: float, half_width: float, color: str = P.PARAM,
         fill_opacity: float = 0.12, stroke_width: float = 2,
         y_span: tuple[float, float] | None = None) -> Rectangle:
    """Vertical band covering |x - x0| < half_width.

    Spans the axes' full y-range by default; pass y_span=(lo, hi) in data units to keep it
    clear of the x-axis line and the top tick.
    """
    y_lo, y_hi = y_span if y_span is not None else (axes.y_range[0], axes.y_range[1])
    if y_lo >= y_hi:
        raise ValueError("y_span must be (lo, hi) with lo < hi")
    left, right = axes.c2p(x0 - half_width, y_lo), axes.c2p(x0 + half_width, y_hi)
    rect = Rectangle(width=abs(right[0] - left[0]), height=abs(right[1] - left[1]),
                     stroke_color=color, stroke_width=stroke_width,
                     fill_color=color, fill_opacity=fill_opacity)
    return rect.move_to((left + right) / 2)


def conditional_fit(xs, ys, x0: float, half_width: float) -> stats.NormalFit:
    """Local Normal fit of y for points in the band (see stats.local_normal)."""
    return stats.local_normal(xs, ys, x0, half_width)


def conditional_slice(axes, xs, ys, x0: float, half_width: float, **slice_kw) -> GaussianSlice:
    """GaussianSlice at x0 fitted to the points inside the band."""
    fit = conditional_fit(xs, ys, x0, half_width)
    return GaussianSlice(axes, x0, fit.mean, fit.sd, **slice_kw)


def mean_point(axes, xs, ys, x0: float, half_width: float):
    """Scene point (x0, local mean) — trace this to draw the regression curve."""
    return axes.c2p(x0, conditional_fit(xs, ys, x0, half_width).mean)
