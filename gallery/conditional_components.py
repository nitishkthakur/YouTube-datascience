"""Gallery: the conditioning components on synthetic data (dsanim.data.linear_gaussian).

Shows, without narration: a Scatter, its marginal GaussianSlice on the y-axis (mu line and
sigma segment labelled), a band with the points inside it focused, the conditional slice
fitted to that band, and the local-mean trace across a short sweep. This is the visual
regression reference for src/dsanim/components/{gaussian,scatter,conditional}.py.

Render: uv run python tools/render.py gallery/conditional_components.py ConditionalComponents -q m --sheet
"""

from manim import (LEFT, RIGHT, Axes, Create, Dot, FadeIn, TracedPath, ValueTracker, VGroup,
                   always_redraw, linear)

from dsanim import data, palette as P, stats, typography as T
from dsanim.components.conditional import band, conditional_slice, mean_point
from dsanim.components.gaussian import GaussianSlice
from dsanim.components.scatter import Scatter
from dsanim.scene import DSScene

HALF_WIDTH = 0.6
PEAK = 1.0


class ConditionalComponents(DSScene):
    def construct(self):
        L = self.layout
        x, y = data.linear_gaussian(n=300, seed=11)
        axes = Axes(x_range=[-1, 7, 1], y_range=[0, 7, 1],
                    x_length=L.plot.width - 1.0, y_length=L.plot.height - 1.0,
                    axis_config={"color": P.MUTED, "stroke_width": 2, "include_tip": False})
        L.plot.fit(axes.move_to(L.plot.center))
        scatter = Scatter(axes, x, y)
        self.add(axes)
        self.play(FadeIn(scatter), run_time=P.ENTRANCE_TIME)

        # marginal on the y-axis (x = -1), labelled
        fit = stats.normal_fit(y)
        marginal = GaussianSlice(axes, -1, fit.mean, fit.sd, peak_width=PEAK)
        labels = VGroup(T.symbol("mu", color=P.CONCEPT).next_to(marginal.mean_line(), RIGHT, 0.1),
                        T.symbol("sigma", color=P.CONCEPT).next_to(marginal.sigma_segment(), LEFT, 0.1))
        self.play(Create(marginal.curve), FadeIn(marginal.fill), run_time=P.RUN_TIME)
        self.play(Create(marginal.mean_line()), Create(marginal.sigma_segment()), FadeIn(labels),
                  run_time=P.ENTRANCE_TIME)

        # band + conditional slice at x = 3, then a short sweep leaving the mean trace
        t = ValueTracker(3.0)
        live_band = always_redraw(lambda: band(axes, t.get_value(), HALF_WIDTH, y_span=(0.3, 6.7)))
        live_slice = always_redraw(lambda: conditional_slice(
            axes, x, y, t.get_value(), HALF_WIDTH, peak_width=PEAK, side=-1))
        scatter.add_updater(lambda m: m.focus_band(t.get_value(), HALF_WIDTH))
        self.play(FadeIn(live_band), run_time=P.ENTRANCE_TIME)
        self.add(live_slice)
        self.wait(P.RUN_TIME)
        trace = TracedPath(lambda: mean_point(axes, x, y, t.get_value(), HALF_WIDTH),
                           stroke_color=P.MODEL, stroke_width=5)
        mean_dot = always_redraw(lambda: Dot(mean_point(axes, x, y, t.get_value(), HALF_WIDTH),
                                             radius=0.06, color=P.MODEL))
        self.add(trace, mean_dot)
        self.play(t.animate.set_value(5.5), run_time=3.0, rate_func=linear)
        scatter.clear_updaters()
        self.wait(P.RUN_TIME)
