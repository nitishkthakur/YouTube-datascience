"""Scene 5 — "Regression, restated". Spec: ../shotlist.md."""

from manim import DOWN, LEFT, FadeIn, FadeOut, VGroup

from common.stage import BAND_Y, GEN_TERMS, HALF_WIDTH, SWEEP, build_stage, roles_for
from dsanim import palette as P, typography as T
from dsanim.components.conditional import SIGMA_FLOOR, band
from dsanim.components.gaussian import GaussianSlice
from dsanim.scene import DSScene

LINES = [
    "Regression predicts a conditional distribution.",
    "OLS: Normal, constant width, centre only.",
    "Next: drop those assumptions, one at a time.",
]


class Scene05(DSScene):
    def construct(self):
        st = build_stage(self)
        axes, scatter = st.axes, st.scatter
        x_end = SWEEP[1]
        line = st.line()
        the_band = band(axes, x_end, HALF_WIDTH, y_span=BAND_Y)
        scatter.focus_band(x_end, HALF_WIDTH)
        fit = st.local_fit(x_end)
        floor = SIGMA_FLOOR * (axes.y_range[1] - axes.y_range[0])
        ols_slice = GaussianSlice(axes, x_end, st.line_y(x_end), st.sigma, peak_width=st.peak, side=1, color=P.MODEL)
        real_slice = GaussianSlice(axes, x_end, fit.mean, max(fit.sd, floor), peak_width=st.peak, side=-1,
                                   color=P.CONCEPT)
        plot_side = VGroup(st.chart, scatter, line, the_band, ols_slice, real_slice)
        eq_gen = st.place_eq(self.eq("general", terms=GEN_TERMS, roles=roles_for(GEN_TERMS)))
        self.add(plot_side, eq_gen)                          # ≈ Scene 4's last frame (ledger aside)

        cards = VGroup(*[T.text(s, size=P.SIZE_BODY) for s in LINES]).arrange(DOWN, buff=0.6, aligned_edge=LEFT)
        st.layout.plot.fit(cards, pad=0.3)

        # --- Beat 5.1 — restated ----------------------------------------------------------------
        with self.beat("5.1", extend=1.0) as b:
            self.play(FadeOut(plot_side), run_time=P.RUN_TIME)   # end card: text where the plot was
            b.wait_until("dist")
            self.play(FadeIn(cards[0]), run_time=P.ENTRANCE_TIME)
            b.wait_until("ols")
            self.play(FadeIn(cards[1]), run_time=P.ENTRANCE_TIME)

        # --- Beat 5.2 — what comes next -------------------------------------------------------
        with self.beat("5.2", extend=2.0) as b:
            b.wait_until("next")
            self.play(FadeIn(cards[2]), run_time=P.ENTRANCE_TIME)
