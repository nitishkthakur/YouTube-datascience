"""Frame orientation, safe area, and the named layout regions.

The short side of the frame is always 8 units, so pixels-per-unit is identical in both
orientations:
  landscape 16:9  frame 14.222 x 8.0   (1920x1080 -> 135 px/unit)
  vertical  9:16  frame 8.0 x 14.222   (1080x1920 -> 135 px/unit)
so a font_size or a stroke width looks the same size in a Short as in the long video.

Orientation is chosen by the environment variable DSANIM_VERTICAL=1 (set by
tools/render.py --vertical), because Manim's CLI cannot pass arguments to a Scene and the
frame must be configured before the Scene's camera exists. dsanim.scene calls
`apply_orientation()` at import time.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np
from manim import config

LONG_SIDE = 8.0 * 16 / 9  # 14.222...
SHORT_SIDE = 8.0
SAFE_MARGIN = 0.05        # nothing within 5% of any edge (AGENTS.md §4)


def is_vertical() -> bool:
    return os.environ.get("DSANIM_VERTICAL", "0") == "1"


def apply_orientation(vertical: bool | None = None) -> None:
    """Configure frame (and pixel) dimensions for the requested orientation."""
    vertical = is_vertical() if vertical is None else vertical
    pw, ph = config.pixel_width, config.pixel_height
    if vertical:
        config.frame_width, config.frame_height = SHORT_SIDE, LONG_SIDE
        if pw > ph:
            config.pixel_width, config.pixel_height = ph, pw
    else:
        config.frame_width, config.frame_height = LONG_SIDE, SHORT_SIDE
        if ph > pw:
            config.pixel_width, config.pixel_height = ph, pw


@dataclass(frozen=True)
class Region:
    """An axis-aligned box in scene coordinates."""

    name: str
    left: float
    right: float
    bottom: float
    top: float

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.top - self.bottom

    @property
    def center(self) -> np.ndarray:
        return np.array([(self.left + self.right) / 2, (self.bottom + self.top) / 2, 0.0])

    def contains(self, mobject, tol: float = 1e-6) -> bool:
        """True if the mobject's bounding box lies inside this region."""
        return (
            mobject.get_left()[0] >= self.left - tol
            and mobject.get_right()[0] <= self.right + tol
            and mobject.get_bottom()[1] >= self.bottom - tol
            and mobject.get_top()[1] <= self.top + tol
        )

    def fit(self, mobject, pad: float = 0.0, scale_up: bool = False):
        """Scale (down, or also up if scale_up) and centre the mobject inside the region."""
        w, h = self.width - 2 * pad, self.height - 2 * pad
        factor = min(w / max(mobject.width, 1e-9), h / max(mobject.height, 1e-9))
        if factor < 1 or scale_up:
            mobject.scale(factor)
        return mobject.move_to(self.center)

    def split_h(self, fraction: float, names: tuple[str, str], gap: float = 0.0):
        """Split left/right at `fraction` of the width."""
        x = self.left + fraction * self.width
        return (
            Region(names[0], self.left, x - gap / 2, self.bottom, self.top),
            Region(names[1], x + gap / 2, self.right, self.bottom, self.top),
        )

    def split_v(self, fractions: list[float], names: list[str], gap: float = 0.0):
        """Split top-to-bottom into bands with the given height fractions (sum to 1)."""
        assert abs(sum(fractions) - 1) < 1e-6 and len(fractions) == len(names)
        regions, top = [], self.top
        for i, (f, n) in enumerate(zip(fractions, names)):
            bottom = top - f * self.height
            regions.append(
                Region(n, self.left, self.right,
                       bottom + (gap / 2 if i < len(names) - 1 else 0),
                       top - (gap / 2 if i > 0 else 0))
            )
            top = bottom
        return regions


def frame() -> Region:
    w, h = config.frame_width, config.frame_height
    return Region("frame", -w / 2, w / 2, -h / 2, h / 2)


def safe() -> Region:
    """The 90% box. Everything visible must live inside it."""
    f = frame()
    mx, my = SAFE_MARGIN * f.width, SAFE_MARGIN * f.height
    return Region("safe", f.left + mx, f.right - mx, f.bottom + my, f.top - my)


@dataclass(frozen=True)
class Layout:
    safe: Region
    plot: Region
    equation: Region
    caption: Region | None  # only in vertical


def regions(vertical: bool | None = None) -> Layout:
    """Default layouts (AGENTS.md §4).

    landscape: plot left ~60% / equation panel right ~40%
    vertical:  plot top ~60% / equation ~30% / caption band ~10%
    """
    vertical = is_vertical() if vertical is None else vertical
    s = safe()
    if vertical:
        plot, eq, cap = s.split_v([0.6, 0.3, 0.1], ["plot", "equation", "caption"], gap=0.2)
        return Layout(s, plot, eq, cap)
    plot, eq = s.split_h(0.6, ("plot", "equation"), gap=0.3)
    return Layout(s, plot, eq, None)
