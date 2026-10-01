"""The channel's standard chart stage: axes with quiet tick numbers and titles fitted into the
plot region, the equation panel split into equation + ledger, and the geometry helpers every
scatter-based scene needs. Topics keep only their constants (ranges, ticks, datasets) in
`common/stage.py`; the construction lives here so 30 topics do not carry 30 copies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from manim import DOWN, LEFT, UP, Axes, VGroup

from dsanim import palette as P, typography as T
from dsanim.layout import Layout, Region


@dataclass(frozen=True)
class ChartSpec:
    x_range: tuple[float, float, float]
    y_range: tuple[float, float, float]
    x_ticks: tuple[float, ...]
    y_ticks: tuple[float, ...]
    x_title: str
    y_title: str
    fmt: Callable[[float], str] = field(default=lambda v: f"{v:g}")


@dataclass
class Chart:
    axes: Axes
    group: VGroup          # axes + tick numbers + titles, already fitted into the plot region

    def c2p(self, x, y):
        return self.axes.c2p(x, y)


def build_chart(layout: Layout, spec: ChartSpec, pad_x: float = 1.0, pad_y: float = 1.5) -> Chart:
    """Axes sized to the plot region minus room for tick numbers and titles, then fitted."""
    L = layout
    axes = Axes(x_range=list(spec.x_range), y_range=list(spec.y_range),
                x_length=L.plot.width - pad_x, y_length=L.plot.height - pad_y,
                axis_config={"color": P.MUTED, "stroke_width": 2, "include_tip": False})
    x_nums = VGroup(*[T.text(spec.fmt(v), size=P.SIZE_TICK, color=P.MUTED).next_to(axes.c2p(v, spec.y_range[0]), DOWN, 0.15)
                      for v in spec.x_ticks])
    y_nums = VGroup(*[T.text(spec.fmt(v), size=P.SIZE_TICK, color=P.MUTED).next_to(axes.c2p(spec.x_range[0], v), LEFT, 0.15)
                      for v in spec.y_ticks])
    x_title = T.label(spec.x_title, color=P.MUTED).next_to(x_nums, DOWN, 0.2)
    x_title.align_to(axes.c2p(spec.x_range[1], spec.y_range[0]), [1, 0, 0])
    y_title = T.label(spec.y_title, color=P.MUTED).next_to(y_nums, UP, 0.25).align_to(y_nums, LEFT)
    group = VGroup(axes, x_nums, y_nums, x_title, y_title)
    L.plot.fit(group.move_to(L.plot.center))
    return Chart(axes, group)


def equation_panel(layout: Layout, split: tuple[float, float] = (0.45, 0.55), gap: float = 0.2
                   ) -> tuple[Region, Region]:
    """(equation region, ledger region): the equation panel split top/bottom."""
    eq, ledger = layout.equation.split_v(list(split), ["eq", "ledger"], gap=gap)
    return eq, ledger


def place_equation(eq, region: Region, max_scale: float = 1.3, pad: tuple[float, float] = (0.3, 0.2)):
    """Centre an equation in its region, scaled to fill it (never clipped, never above max_scale)."""
    scale = min(max_scale, (region.width - pad[0]) / eq.width, (region.height - pad[1]) / eq.height)
    return eq.scale(scale).move_to(region.center)


def peak_room(layout: Layout, axes: Axes, x_edge: float, max_peak: float, margin: float = 0.1) -> float:
    """Largest Gaussian-slice peak width that keeps a right-bulging slice at data x = x_edge
    inside the safe area (the 9:16 frame is narrow)."""
    room = float(layout.safe.right - axes.c2p(x_edge, axes.y_range[0])[0] - margin)
    return max(0.2, min(max_peak, room))
