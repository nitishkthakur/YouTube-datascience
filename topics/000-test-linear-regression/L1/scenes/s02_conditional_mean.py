"""Scene 2 — "The line is a conditional mean". Spec: ../shotlist.md."""

import numpy as np
from manim import (RIGHT, UP, Dot, FadeIn, FadeOut, GrowFromCenter, Indicate, TracedPath,
                   ValueTracker, linear, smooth)

from common.stage import (BAND_X, BAND_Y, COND_TERMS, HALF_WIDTH, LINE_TERMS, SWEEP, build_stage,
                          roles_for)
from dsanim import palette as P, typography as T
from dsanim.components.conditional import band, conditional_fit
from dsanim.components.equations import morph
from dsanim.components.ledger import Ledger
from dsanim.scene import DSScene


class Scene02(DSScene):
    def construct(self):
        st = build_stage(self)
        axes, scatter = st.axes, st.scatter
        line = st.line()
        eq_line = st.place_eq(self.eq("line", terms=LINE_TERMS, roles=roles_for(LINE_TERMS)))
        self.add(st.chart, scatter, line, eq_line)          # = Scene 1's last frame

        # --- Beat 2.1 — pick a weight ---------------------------------------------------------
        with self.beat("2.1", extend=1.5) as b:
            b.wait_until("band")
            the_band = band(axes, BAND_X, HALF_WIDTH, y_span=BAND_Y)
            label = T.label(f"{BAND_X} kg", color=P.PARAM)
            label.next_to(the_band, RIGHT, 0.12).align_to(the_band, UP)
            self.play(FadeIn(the_band), FadeIn(label), run_time=P.ENTRANCE_TIME)
            self.play(scatter.animate.focus_band(BAND_X, HALF_WIDTH), run_time=P.ENTRANCE_TIME)

        # --- Beat 2.2 — their average is one number ---------------------------------------------
        x = ValueTracker(BAND_X)
        inside = np.abs(st.wx - BAND_X) < HALF_WIDTH
        in_dots = [d for d, keep in zip(scatter, inside) if keep]
        home = [d.get_center().copy() for d in in_dots]

        def local_mean():
            return conditional_fit(st.wx, st.mpg, x.get_value(), HALF_WIDTH).mean

        with self.beat("2.2", extend=1.5) as b:
            b.wait_until("mean")
            self.play(*[d.animate.move_to(axes.c2p(BAND_X, y))
                        for d, y in zip(in_dots, st.mpg[inside])], run_time=P.ENTRANCE_TIME)
            mean_dot = Dot(axes.c2p(BAND_X, local_mean()), radius=0.09, color=P.CONCEPT)
            self.play(GrowFromCenter(mean_dot), run_time=P.ENTRANCE_TIME)
            ledger = Ledger([
                ("x", x.get_value, {"decimals": 0, "unit": "kg", "color": P.PARAM}),
                ("mu(x)", local_mean, {"decimals": 1, "color": P.CONCEPT}),
                ("hat y", lambda: st.line_y(x.get_value()), {"decimals": 1, "color": P.MODEL}),
            ], region=st.ledger_region)
            self.play(FadeIn(ledger), run_time=P.ENTRANCE_TIME)

        # --- Beat 2.3 — slide the weight: the means trace a path ---------------------------------
        with self.beat("2.3", extend=6.0) as b:
            self.play(*[d.animate.move_to(p) for d, p in zip(in_dots, home)], FadeOut(label),
                      run_time=0.6)
            b.wait_until("slide")
            the_band.add_updater(lambda m: m.become(band(axes, x.get_value(), HALF_WIDTH, y_span=BAND_Y)))
            scatter.add_updater(lambda m: m.focus_band(x.get_value(), HALF_WIDTH))
            mean_dot.add_updater(lambda m: m.move_to(axes.c2p(x.get_value(), local_mean())))
            ledger.live()
            trace = TracedPath(mean_dot.get_center, stroke_color=P.CONCEPT, stroke_width=5)
            self.add(trace)
            self.play(x.animate.set_value(SWEEP[0]), run_time=1.5, rate_func=smooth)
            self.play(x.animate.set_value(SWEEP[1]), run_time=5.0, rate_func=linear)
            for m in (the_band, scatter, mean_dot, ledger, trace):
                m.clear_updaters()
            eq_cond = st.place_eq(self.eq("condmean", terms=COND_TERMS, roles=roles_for(COND_TERMS)))
            self.play(morph(eq_line, eq_cond), run_time=P.RUN_TIME)

        # --- Beat 2.4 — close, not exact ------------------------------------------------------
        with self.beat("2.4", extend=1.5) as b:
            self.play(Indicate(trace, color=P.CONCEPT, scale_factor=1.0), run_time=P.RUN_TIME)
            self.play(FadeOut(the_band), FadeOut(trace), FadeOut(mean_dot), FadeOut(ledger),
                      scatter.animate.unfocus(), run_time=P.ENTRANCE_TIME)
