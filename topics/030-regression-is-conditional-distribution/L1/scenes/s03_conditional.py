"""Scene 3 — "From marginal to conditional" (the AGENTS.md §13 pilot).

Spec: ../shotlist.md (Scene 3). Narration + equations: ../script.md.
Data: UCI Auto MPG, all 398 cars, weight in kg (dsanim.data.auto_mpg).

Render: uv run python tools/render.py \
    topics/030-regression-is-conditional-distribution/L1/scenes/s03_conditional.py Scene03 -q m --sheet
"""

from manim import (DOWN, LEFT, RIGHT, UP, Axes, Create, Dot, FadeIn, FadeOut, TracedPath, Transform,
                   ValueTracker, VGroup, Write, linear, smooth, there_and_back)

from dsanim import data, palette as P, stats, typography as T
from dsanim.components.conditional import band, conditional_fit, conditional_slice, mean_point
from dsanim.components.equations import morph
from dsanim.components.gaussian import GaussianSlice
from dsanim.components.ledger import Ledger
from dsanim.components.scatter import Scatter
from dsanim.scene import DSScene

# --- Shot-list parameters (shotlist.md, Scene 3) ---------------------------------------
X_RANGE = (500, 2500, 500)   # kg — empty strip left of the data holds the collapsed points
Y_RANGE = (0, 50, 10)        # mpg
BAND_X = 1500                # kg, from the narration
HALF_WIDTH = 75              # kg -> 150 kg band (⚑ was ≈100)
SWEEP = (900, 2200)          # kg
SLIDE_LEFT = 2.0             # s, band slides 1500 -> 900 (no teleport)
SWEEP_TIME = 5.0             # s, 900 -> 2200
PEAK = 1.3                   # scene units — shared peak width of every Gaussian slice
BAND_Y = (2, 48)             # mpg — band stays clear of the x-axis line and the top tick

MARG_TERMS = ["Y", r"\sim", r"\mathcal{N}(", r"\mu", ",", r"\sigma", "^2)"]
COND_TERMS = ["Y", r"\mid X=x", r"\sim", r"\mathcal{N}(", r"\mu(x)", ",", r"\sigma(x)", "^2)"]
ROLES = {r"\mid X=x": P.PARAM, r"\mu": P.CONCEPT, r"\mu(x)": P.CONCEPT,
         r"\sigma": P.CONCEPT, r"\sigma(x)": P.CONCEPT}


def roles_for(terms):
    return {t: ROLES[t] for t in terms if t in ROLES}


class Scene03(DSScene):
    def construct(self):
        L = self.layout
        cars = data.auto_mpg()
        wx, mpg = cars["weight_kg"].to_numpy(), cars["mpg"].to_numpy()

        # --- Persistent: axes + scatter (carried over from Scene 2) --------------------------
        axes = Axes(x_range=X_RANGE, y_range=Y_RANGE,
                    x_length=L.plot.width - 1.0, y_length=L.plot.height - 1.7,
                    axis_config={"color": P.MUTED, "stroke_width": 2, "include_tip": False})
        x_nums = VGroup(*[T.text(f"{v}", size=P.SIZE_TICK, color=P.MUTED).next_to(axes.c2p(v, 0), DOWN, 0.15)
                          for v in (1000, 1500, 2000)])
        y_nums = VGroup(*[T.text(f"{v}", size=P.SIZE_TICK, color=P.MUTED).next_to(axes.c2p(X_RANGE[0], v), LEFT, 0.15)
                          for v in (10, 20, 30, 40, 50)])
        x_title = T.label("weight (kg)", color=P.MUTED).next_to(x_nums, DOWN, 0.2)
        x_title.align_to(axes.c2p(X_RANGE[1], 0), RIGHT)
        y_title = T.label("mpg", color=P.MUTED).next_to(y_nums, UP, 0.25).align_to(y_nums, LEFT)
        chart = VGroup(axes, x_nums, y_nums, x_title, y_title)
        L.plot.fit(chart.move_to(L.plot.center))
        scatter = Scatter(axes, wx, mpg)
        self.add(chart, scatter)

        eq_region, ledger_region = L.equation.split_v([0.45, 0.55], ["eq", "ledger"], gap=0.2)
        eq_marginal = eq_region.fit(self.eq("marginal", terms=MARG_TERMS, roles=roles_for(MARG_TERMS)), pad=0.15)
        eq_conditional = eq_region.fit(self.eq("conditional", terms=COND_TERMS, roles=roles_for(COND_TERMS)), pad=0.15)

        # --- Beat 3.1 — ignore x: collapse onto the y-axis, fit the marginal Normal ----------
        with self.beat("3.1", extend=2.0) as b:
            # collapse lasts exactly until "Here is every mpg value..." is spoken
            self.play(Transform(scatter, scatter.collapsed(X_RANGE[0])), run_time=b.until("values"))
            fit = stats.normal_fit(mpg)
            marginal = GaussianSlice(axes, X_RANGE[0], fit.mean, fit.sd, peak_width=PEAK, side=1)
            mu_line, sigma_seg = marginal.mean_line(), marginal.sigma_segment()
            mu_label = T.symbol("mu", color=P.CONCEPT).next_to(mu_line, RIGHT, 0.15)
            sigma_label = T.symbol("sigma", color=P.CONCEPT).next_to(sigma_seg, LEFT, 0.12)
            self.play(marginal.appear(), run_time=P.RUN_TIME)
            self.play(Create(mu_line), FadeIn(mu_label), Create(sigma_seg), FadeIn(sigma_label),
                      run_time=P.ENTRANCE_TIME)
            self.play(Write(eq_marginal), run_time=P.RUN_TIME)
        marginal_group = VGroup(marginal, mu_line, sigma_seg, mu_label, sigma_label)

        # --- Beat 3.2 — condition on x = 1500 kg ---------------------------------------------
        x = ValueTracker(BAND_X)

        def local():
            return conditional_fit(wx, mpg, x.get_value(), HALF_WIDTH)

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
            self.play(cond.appear(), run_time=P.RUN_TIME)
            self.play(morph(eq_marginal, eq_conditional), run_time=P.RUN_TIME)
            ledger = Ledger([
                ("x", x.get_value, {"decimals": 0, "unit": "kg", "color": P.PARAM}),
                ("mu(x)", lambda: local().mean, {"decimals": 1, "color": P.CONCEPT}),
                ("sigma(x)", lambda: local().sd, {"decimals": 1, "color": P.CONCEPT}),
                ("n", lambda: local().n, {"decimals": 0, "color": P.TEXT}),
            ], region=ledger_region)
            self.play(FadeIn(ledger), run_time=P.ENTRANCE_TIME)

        # --- Beat 3.3 — slide x: the mean traces the regression curve ------------------------
        with self.beat("3.3", extend=9.0) as b:
            the_band.add_updater(lambda m: m.become(band(axes, x.get_value(), HALF_WIDTH, y_span=BAND_Y)))
            scatter.add_updater(lambda m: m.focus_band(x.get_value(), HALF_WIDTH))

            def follow(m):
                f = local()
                m.set_params(x0=x.get_value(), mu=f.mean, sigma=max(f.sd, 0.02 * (Y_RANGE[1] - Y_RANGE[0])))

            cond.add_updater(follow)
            ledger.live()

            def mean_here():
                return mean_point(axes, wx, mpg, x.get_value(), HALF_WIDTH)

            trace = TracedPath(mean_here, stroke_color=P.MODEL, stroke_width=5)
            mean_dot = Dot(mean_here(), radius=0.06, color=P.MODEL)
            mean_dot.add_updater(lambda m: m.move_to(mean_here()))
            self.add(trace, mean_dot)
            # the ledger's live x replaces the static label; drop it before anything moves
            self.play(FadeOut(band_label), run_time=0.4)
            # no teleport: slide left to 900, then sweep right to 2200; the trace grows both ways
            self.play(x.animate.set_value(SWEEP[0]), run_time=SLIDE_LEFT, rate_func=smooth)
            self.play(x.animate.set_value(SWEEP[1]), run_time=SWEEP_TIME, rate_func=linear)
            for m in (the_band, scatter, cond, ledger, mean_dot, trace):
                m.clear_updaters()
            self.wait(max(b.remaining - P.RUN_TIME, 0.0))
            self.play(trace.animate(rate_func=there_and_back).set_stroke(width=12), run_time=P.RUN_TIME)
