"""Scene 3 — "What the line leaves out". Spec: ../shotlist.md."""

import numpy as np
from manim import LEFT, BraceBetweenPoints, Create, FadeIn, FadeOut, Indicate, LaggedStart, Line, VGroup

from common.stage import BAND_X, BAND_Y, COND_TERMS, HALF_WIDTH, NOISE_TERMS, build_stage, roles_for
from dsanim import palette as P, typography as T
from dsanim.components.conditional import band
from dsanim.components.equations import morph
from dsanim.scene import DSScene


class Scene03(DSScene):
    def construct(self):
        st = build_stage(self)
        axes, scatter = st.axes, st.scatter
        line = st.line()
        eq_cond = st.place_eq(self.eq("condmean", terms=COND_TERMS, roles=roles_for(COND_TERMS)))
        self.add(st.chart, scatter, line, eq_cond)          # = Scene 2's last frame

        # --- Beat 3.1 — residuals -------------------------------------------------------------
        inside = np.abs(st.wx - BAND_X) < HALF_WIDTH
        with self.beat("3.1", extend=1.5) as b:
            the_band = band(axes, BAND_X, HALF_WIDTH, y_span=BAND_Y)
            self.play(FadeIn(the_band), scatter.animate.focus_band(BAND_X, HALF_WIDTH),
                      run_time=P.ENTRANCE_TIME)
            b.wait_until("residuals")
            sticks = VGroup(*[
                Line(axes.c2p(xi, yi), axes.c2p(xi, st.line_y(xi)), color=P.ERROR, stroke_width=2.5)
                for xi, yi in zip(st.wx[inside], st.mpg[inside])])
            self.play(LaggedStart(*[Create(s) for s in sticks], lag_ratio=0.03), run_time=1.0)

        # --- Beat 3.2 — sigma -----------------------------------------------------------------
        with self.beat("3.2", extend=2.0) as b:
            b.wait_until("sigma")
            y0 = st.line_y(BAND_X)
            left_x = BAND_X - HALF_WIDTH - 30
            bracket = BraceBetweenPoints(axes.c2p(left_x, y0 - st.sigma), axes.c2p(left_x, y0 + st.sigma),
                                         direction=LEFT, color=P.CONCEPT)
            sigma_label = T.symbol("sigma", color=P.CONCEPT).next_to(bracket, LEFT, 0.1)
            self.play(FadeIn(bracket), FadeIn(sigma_label), run_time=P.ENTRANCE_TIME)
            eq_noise = st.place_eq(self.eq("noise", terms=NOISE_TERMS, roles=roles_for(NOISE_TERMS)))
            self.play(morph(eq_cond, eq_noise), run_time=P.RUN_TIME)

        # --- Beat 3.3 — not an error ------------------------------------------------------------
        with self.beat("3.3", extend=1.0) as b:
            self.play(FadeOut(sticks), run_time=P.ENTRANCE_TIME)
            self.play(Indicate(VGroup(bracket, sigma_label), color=P.CONCEPT, scale_factor=1.1),
                      run_time=P.RUN_TIME)
