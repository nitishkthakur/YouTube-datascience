"""The shared stage for every scene of this tier.

One builder, so every scene has the same axes, the same 398 cars, the same line and the same
equation panel positions — nothing jumps between scenes (shot list TRANSITION rows; the seam
check in tools/assemble.py). Scenes import it via the tier folder, which tools/render.py
puts on PYTHONPATH: `from common.stage import build_stage`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from manim import DOWN, LEFT, UP, Axes, VGroup

from dsanim import data, palette as P, stats, typography as T
from dsanim.components.scatter import Scatter
from dsanim.layout import Layout, Region

X_RANGE = (500, 2500, 500)    # kg
Y_RANGE = (0, 50, 10)         # mpg
LINE_X = (700, 2400)          # kg: draw the line only where there are cars
BAND_X = 1500                 # kg, from the narration
HALF_WIDTH = 75               # kg -> 150 kg band
BAND_Y = (2, 48)              # mpg: band clear of the x-axis line and the top tick
PEAK_MAX = 1.3                # scene units: shared peak width of every Gaussian slice (landscape)
SWEEP = (900, 2200)           # kg

# Equation tokenisation for term-wise reveal/morph (must concatenate to the script's LaTeX).
LINE_TERMS = [r"\hat{y}", "=", r"\beta_0", "+", r"\beta_1", "x"]
COND_TERMS = [r"\mathbb{E}[Y \mid X=x]", "=", r"\beta_0", "+", r"\beta_1", "x"]
NOISE_TERMS = ["Y", "=", r"\beta_0", "+", r"\beta_1", "x", "+", r"\varepsilon", r",\qquad",
               r"\varepsilon", r"\sim", r"\mathcal{N}(0,", r"\sigma", "^2)"]
OLS_TERMS = ["Y", r"\mid X=x", r"\sim", r"\mathcal{N}(", r"\beta_0", "+", r"\beta_1", "x", ",",
             r"\sigma", "^2)"]
GEN_TERMS = ["Y", r"\mid X=x", r"\sim", r"\mathcal{N}(", r"\mu(x)", ",", r"\sigma(x)", "^2)"]

# Colour roles for terms: the panel speaks the plot's colour language (AGENTS.md §4).
ROLES = {
    r"\hat{y}": P.MODEL, r"\beta_0": P.MODEL, r"\beta_1": P.MODEL,          # the line
    "x": P.PARAM, r"\mid X=x": P.PARAM,                                      # the conditioning value
    r"\mathbb{E}[Y \mid X=x]": P.CONCEPT, r"\mu(x)": P.CONCEPT,              # the conditional centre
    r"\sigma": P.CONCEPT, r"\sigma(x)": P.CONCEPT,                           # the spread
    r"\varepsilon": P.ERROR,                                                 # "noise"
}


def roles_for(terms: list[str]) -> dict[str, str]:
    return {t: ROLES[t] for t in terms if t in ROLES}


@dataclass
class Stage:
    layout: Layout
    axes: Axes
    chart: VGroup            # axes + tick numbers + titles
    scatter: Scatter
    wx: np.ndarray
    mpg: np.ndarray
    b0: float
    b1: float
    sigma: float             # OLS residual sd (ddof = 2)
    eq_region: Region        # upper part of the equation panel
    ledger_region: Region    # lower part: live readouts
    peak: float              # Gaussian slice peak width that stays inside the safe area at the sweep's end

    def line_y(self, x: float) -> float:
        return self.b0 + self.b1 * x

    def line(self, **kw):
        return self.axes.plot(self.line_y, x_range=list(LINE_X), color=P.MODEL, stroke_width=5, **kw)

    def place_eq(self, eq):
        """Centre an equation in the panel, scaled down only if it is too wide."""
        return self.eq_region.fit(eq, pad=0.15)

    def local_fit(self, x0: float) -> stats.NormalFit:
        return stats.local_normal(self.wx, self.mpg, x0, HALF_WIDTH)


def build_stage(scene) -> Stage:
    L = scene.layout
    cars = data.auto_mpg()
    wx, mpg = cars["weight_kg"].to_numpy(), cars["mpg"].to_numpy()
    b1, b0 = np.polyfit(wx, mpg, 1)
    sigma = float(np.std(mpg - (b0 + b1 * wx), ddof=2))

    axes = Axes(x_range=X_RANGE, y_range=Y_RANGE,
                x_length=L.plot.width - 1.0, y_length=L.plot.height - 1.7,
                axis_config={"color": P.MUTED, "stroke_width": 2, "include_tip": False})
    x_nums = VGroup(*[T.text(f"{v}", size=P.SIZE_TICK, color=P.MUTED).next_to(axes.c2p(v, 0), DOWN, 0.15)
                      for v in (1000, 1500, 2000)])
    y_nums = VGroup(*[T.text(f"{v}", size=P.SIZE_TICK, color=P.MUTED).next_to(axes.c2p(X_RANGE[0], v), LEFT, 0.15)
                      for v in (10, 20, 30, 40, 50)])
    x_title = T.label("weight (kg)", color=P.MUTED).next_to(x_nums, DOWN, 0.2)
    x_title.align_to(axes.c2p(X_RANGE[1], 0), [1, 0, 0])
    y_title = T.label("mpg", color=P.MUTED).next_to(y_nums, UP, 0.25).align_to(y_nums, LEFT)
    chart = VGroup(axes, x_nums, y_nums, x_title, y_title)
    L.plot.fit(chart.move_to(L.plot.center))

    eq_region, ledger_region = L.equation.split_v([0.45, 0.55], ["eq", "ledger"], gap=0.2)
    # A right-bulging slice at the far end of the sweep must not leave the safe area (9:16 is narrow).
    room = L.safe.right - axes.c2p(SWEEP[1] + HALF_WIDTH, 0)[0] - 0.1
    peak = min(PEAK_MAX, room)
    return Stage(L, axes, chart, Scatter(axes, wx, mpg), wx, mpg, float(b0), float(b1), sigma,
                 eq_region, ledger_region, peak)
