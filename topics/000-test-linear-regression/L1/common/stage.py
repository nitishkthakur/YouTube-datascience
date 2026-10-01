"""The shared stage for every scene of this tier.

Only the tier's constants live here (ranges, ticks, band, sweep, equation tokens, roles); the
construction is dsanim.components.chart, so every scene has the same axes, cars, line and
panel — nothing jumps between scenes (shot list TRANSITION rows; the seam check in
tools/assemble.py). Scenes import it via the tier folder on PYTHONPATH:
`from common.stage import build_stage`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from manim import Axes, VGroup

from dsanim import data, palette as P, stats
from dsanim.components.chart import ChartSpec, build_chart, equation_panel, peak_room, place_equation
from dsanim.components.equations import roles_for as _roles_for
from dsanim.components.scatter import Scatter
from dsanim.layout import Layout, Region

X_RANGE = (500, 2500, 500)    # kg
Y_RANGE = (0, 50, 10)         # mpg
CHART = ChartSpec(X_RANGE, Y_RANGE, (1000, 1500, 2000), (10, 20, 30, 40, 50), "weight (kg)", "mpg")
LINE_X = (700, 2400)          # kg: draw the line only where there are cars
BAND_X = 1500                 # kg, from the narration
HALF_WIDTH = 75               # kg -> 150 kg band
BAND_Y = (2, 48)              # mpg: band clear of the x-axis line and the top tick
PEAK_MAX = 1.3                # scene units: shared peak width of every Gaussian slice (landscape)
SWEEP = (900, 2200)           # kg
PARK_X = 1300                 # kg: where the band rests after the sweep so both bells stay legible

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
    r"\sigma": P.MODEL,                                                      # OLS's one constant width = the line's
    r"\sigma(x)": P.CONCEPT,                                                 # the real, local spread
    r"\varepsilon": P.ERROR,                                                 # "noise"
}


def roles_for(terms: list[str]) -> dict[str, str]:
    return _roles_for(terms, ROLES)


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
        return place_equation(eq, self.eq_region)

    def local_fit(self, x0: float) -> stats.NormalFit:
        return stats.local_normal(self.wx, self.mpg, x0, HALF_WIDTH)


def build_stage(scene) -> Stage:
    L = scene.layout
    cars = data.auto_mpg()
    wx, mpg = cars["weight_kg"].to_numpy(), cars["mpg"].to_numpy()
    b1, b0 = np.polyfit(wx, mpg, 1)
    sigma = float(np.std(mpg - (b0 + b1 * wx), ddof=2))
    chart = build_chart(L, CHART)
    eq_region, ledger_region = equation_panel(L)
    peak = peak_room(L, chart.axes, SWEEP[1] + HALF_WIDTH, PEAK_MAX)
    return Stage(L, chart.axes, chart.group, Scatter(chart.axes, wx, mpg), wx, mpg, float(b0), float(b1),
                 sigma, eq_region, ledger_region, peak)
