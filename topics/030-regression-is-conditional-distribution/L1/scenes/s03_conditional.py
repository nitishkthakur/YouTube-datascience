"""Scene 3 — "From marginal to conditional" (the AGENTS.md §13 pilot).

Spec: ../shotlist.md (Scene 3). Narration + equations: ../script.md.
Data: UCI Auto MPG, all 398 cars, weight in kg (dsanim.data.auto_mpg).

Render: uv run python tools/render.py \
    topics/030-regression-is-conditional-distribution/L1/scenes/s03_conditional.py Scene03 -q m --sheet
"""

from manim import (DOWN, LEFT, RIGHT, UP, Axes, Create, Dot, FadeIn, FadeOut, TracedPath,
                   Transform, TransformMatchingShapes, ValueTracker, VGroup, Write, always_redraw,
                   linear, smooth, there_and_back)

from dsanim import data, palette as P, stats, typography as T
from dsanim.components.conditional import band, conditional_slice, mean_point
from dsanim.components.gaussian import GaussianSlice
from dsanim.components.scatter import Scatter
from dsanim.scene import DSScene

# --- Shot-list parameters (shotlist.md, Scene 3) ---------------------------------------
X_RANGE = (500, 2500, 500)   # kg — empty strip left of the data holds the collapsed points
Y_RANGE = (0, 50, 10)        # mpg
BAND_X = 1500                # kg, from the narration
HALF_WIDTH = 75              # kg -> 150 kg band (⚑ was ≈100)
SWEEP = (900, 2200)          # kg
SWEEP_TIME = 6.0             # s
RESET_TIME = 1.2             # s, band back to 900 kg before the sweep
HOLD = 3.0                   # s, hold after the sweep
PEAK = 1.3                   # scene units — shared peak width of every Gaussian slice
BAND_Y = (2, 48)             # mpg — band stays clear of the x-axis line and the top tick
COLLAPSE_TIME = 2.0          # s


class Scene03(DSScene):
    def construct(self):
        L = self.layout
        cars = data.auto_mpg()
        wx, mpg = cars["weight_kg"].to_numpy(), cars["mpg"].to_numpy()

        # --- Persistent: axes + scatter (carried over from Scene 2) --------------------------
        # Leave room inside the plot region for tick numbers and axis titles.
        axes = Axes(x_range=X_RANGE, y_range=Y_RANGE,
                    x_length=L.plot.width - 1.0, y_length=L.plot.height - 1.7,
                    axis_config={"color": P.MUTED, "stroke_width": 2, "include_tip": False})
        x_nums = VGroup(*[T.label(f"{v}", color=P.MUTED).next_to(axes.c2p(v, 0), DOWN, 0.15)
                          for v in (1000, 1500, 2000)])
        y_nums = VGroup(*[T.label(f"{v}", color=P.MUTED).next_to(axes.c2p(X_RANGE[0], v), LEFT, 0.15)
                          for v in (10, 20, 30, 40, 50)])
        x_title = T.label("weight (kg)", color=P.MUTED).next_to(x_nums, DOWN, 0.2)
        x_title.align_to(axes.c2p(X_RANGE[1], 0), RIGHT)
        y_title = T.label("mpg", color=P.MUTED).next_to(y_nums, UP, 0.25).align_to(y_nums, LEFT)
        chart = VGroup(axes, x_nums, y_nums, x_title, y_title)
        L.plot.fit(chart.move_to(L.plot.center))  # scales down only if it would not fit
        scatter = Scatter(axes, wx, mpg)
        self.add(axes, x_nums, y_nums, x_title, y_title, scatter)

        # Both equations share one scale so glyphs don't jump during the morph.
        eq_marginal, eq_conditional = self.eq("marginal"), self.eq("conditional")
        scale = min(1.0, (L.equation.width - 0.4) / eq_conditional.width)
        for eq in (eq_marginal, eq_conditional):
            eq.scale(scale).move_to(L.equation.center)

        # --- Beat 3.1 — ignore x: collapse onto the y-axis, fit the marginal Normal ----------
        with self.beat("3.1", extend=2.0) as b:
            self.play(Transform(scatter, scatter.collapsed(X_RANGE[0])), run_time=COLLAPSE_TIME)
            b.wait_until("values")
            fit = stats.normal_fit(mpg)
            marginal = GaussianSlice(axes, X_RANGE[0], fit.mean, fit.sd, peak_width=PEAK, side=1)
            mu_line, sigma_seg = marginal.mean_line(), marginal.sigma_segment()
            mu_label = T.symbol("mu", color=P.CONCEPT).next_to(mu_line, RIGHT, 0.15)
            sigma_label = T.symbol("sigma", color=P.CONCEPT).next_to(sigma_seg, LEFT, 0.12)
            self.play(Create(marginal.curve), FadeIn(marginal.fill), run_time=P.RUN_TIME)
            self.play(Create(mu_line), FadeIn(mu_label), Create(sigma_seg), FadeIn(sigma_label),
                      run_time=P.ENTRANCE_TIME)
            self.play(Write(eq_marginal), run_time=P.RUN_TIME)
        marginal_group = VGroup(marginal, mu_line, sigma_seg, mu_label, sigma_label)

        # --- Beat 3.2 — condition on x = 1500 kg ---------------------------------------------
        with self.beat("3.2", extend=3.0) as b:
            self.play(Transform(scatter, Scatter(axes, wx, mpg)),
                      marginal_group.animate.fade(0.7), run_time=P.RUN_TIME)
            b.wait_until("weighs")
            the_band = band(axes, BAND_X, HALF_WIDTH, y_span=BAND_Y)
            band_label = T.label(f"{BAND_X} kg", color=P.PARAM)
            band_label.next_to(the_band, RIGHT, 0.12).align_to(the_band, UP)
            self.play(FadeIn(the_band), FadeIn(band_label), run_time=P.ENTRANCE_TIME)
            self.play(scatter.animate.focus_band(BAND_X, HALF_WIDTH), run_time=P.ENTRANCE_TIME)
            cond = conditional_slice(axes, wx, mpg, BAND_X, HALF_WIDTH, peak_width=PEAK, side=-1)
            self.play(Create(cond.curve), FadeIn(cond.fill), run_time=P.RUN_TIME)
            self.play(TransformMatchingShapes(eq_marginal, eq_conditional), run_time=P.RUN_TIME)

        # --- Beat 3.3 — slide x: the mean traces the regression curve ------------------------
        with self.beat("3.3", extend=9.0):
            x = ValueTracker(BAND_X)
            live_band = always_redraw(lambda: band(axes, x.get_value(), HALF_WIDTH, y_span=BAND_Y))
            live_slice = always_redraw(lambda: conditional_slice(
                axes, wx, mpg, x.get_value(), HALF_WIDTH, peak_width=PEAK, side=-1))
            # Create/FadeIn added the slice's curve and fill as top-level mobjects.
            self.remove(the_band, cond, cond.curve, cond.fill)
            self.add(live_band, live_slice)
            scatter.add_updater(lambda m: m.focus_band(x.get_value(), HALF_WIDTH))
            self.play(FadeOut(band_label), x.animate.set_value(SWEEP[0]),
                      run_time=RESET_TIME, rate_func=smooth)

            def mean_here():
                return mean_point(axes, wx, mpg, x.get_value(), HALF_WIDTH)

            trace = TracedPath(mean_here, stroke_color=P.MODEL, stroke_width=5)
            mean_dot = always_redraw(lambda: Dot(mean_here(), radius=0.06, color=P.MODEL))
            self.add(trace, mean_dot)
            self.play(x.animate.set_value(SWEEP[1]), run_time=SWEEP_TIME, rate_func=linear)
            for m in (scatter, trace):
                m.clear_updaters()
            self.wait(HOLD)
            self.play(trace.animate(rate_func=there_and_back).set_stroke(width=12),
                      run_time=P.RUN_TIME)
