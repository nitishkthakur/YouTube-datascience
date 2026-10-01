"""Scene 4 — "You were predicting a distribution all along". Spec: ../shotlist.md."""

from manim import LEFT, BraceBetweenPoints, FadeIn, FadeOut, Indicate, ValueTracker, linear, smooth

from common.stage import (BAND_X, BAND_Y, GEN_TERMS, HALF_WIDTH, NOISE_TERMS, OLS_TERMS, SWEEP,
                          build_stage, roles_for)
from dsanim import palette as P, typography as T
from dsanim.components.conditional import SIGMA_FLOOR, band
from dsanim.components.equations import morph
from dsanim.components.gaussian import GaussianSlice
from dsanim.components.ledger import Ledger
from dsanim.scene import DSScene


class Scene04(DSScene):
    def construct(self):
        st = build_stage(self)
        axes, scatter = st.axes, st.scatter
        line = st.line()
        eq_noise = st.place_eq(self.eq("noise", terms=NOISE_TERMS, roles=roles_for(NOISE_TERMS)))
        the_band = band(axes, BAND_X, HALF_WIDTH, y_span=BAND_Y)
        scatter.focus_band(BAND_X, HALF_WIDTH)
        y0 = st.line_y(BAND_X)
        left_x = BAND_X - HALF_WIDTH - 30
        bracket = BraceBetweenPoints(axes.c2p(left_x, y0 - st.sigma), axes.c2p(left_x, y0 + st.sigma),
                                     direction=LEFT, color=P.CONCEPT)
        sigma_label = T.symbol("sigma", color=P.CONCEPT).next_to(bracket, LEFT, 0.1)
        self.add(st.chart, scatter, line, eq_noise, the_band, bracket, sigma_label)  # = Scene 3's last frame

        x = ValueTracker(BAND_X)

        def local():
            return st.local_fit(x.get_value())

        # --- Beat 4.1 — a bell at every weight ----------------------------------------------------
        with self.beat("4.1", extend=1.5) as b:
            b.wait_until("bell")
            ols_slice = GaussianSlice(axes, BAND_X, y0, st.sigma, peak_width=st.peak, side=1, color=P.MODEL)
            self.play(ols_slice.appear(), FadeOut(bracket), FadeOut(sigma_label), run_time=P.RUN_TIME)
            eq_ols = st.place_eq(self.eq("ols", terms=OLS_TERMS, roles=roles_for(OLS_TERMS)))
            self.play(morph(eq_noise, eq_ols), run_time=P.RUN_TIME)

        # --- Beat 4.2 — the rigid bell vs the real one ---------------------------------------------
        with self.beat("4.2", extend=8.0) as b:
            b.wait_until("sweep")
            fit = local()
            floor = SIGMA_FLOOR * (axes.y_range[1] - axes.y_range[0])
            real_slice = GaussianSlice(axes, BAND_X, fit.mean, max(fit.sd, floor), peak_width=st.peak,
                                       side=-1, color=P.CONCEPT)
            ledger = Ledger([
                ("x", x.get_value, {"decimals": 0, "unit": "kg", "color": P.PARAM}),
                ("sigma", lambda: st.sigma, {"decimals": 1, "color": P.MODEL}),
                ("sigma(x)", lambda: local().sd, {"decimals": 1, "color": P.CONCEPT}),
                ("n", lambda: local().n, {"decimals": 0, "color": P.TEXT}),
            ], region=st.ledger_region)
            self.play(real_slice.appear(), FadeIn(ledger), run_time=P.RUN_TIME)

            the_band.add_updater(lambda m: m.become(band(axes, x.get_value(), HALF_WIDTH, y_span=BAND_Y)))
            scatter.add_updater(lambda m: m.focus_band(x.get_value(), HALF_WIDTH))
            ols_slice.add_updater(lambda m: m.set_params(x0=x.get_value(), mu=st.line_y(x.get_value())))

            def follow(m):
                f = local()
                m.set_params(x0=x.get_value(), mu=f.mean, sigma=max(f.sd, floor))

            real_slice.add_updater(follow)
            ledger.live()
            self.play(x.animate.set_value(SWEEP[0]), run_time=1.5, rate_func=smooth)
            self.play(x.animate.set_value(SWEEP[1]), run_time=5.5, rate_func=linear)
            for m in (the_band, scatter, ols_slice, real_slice, ledger):
                m.clear_updaters()

        # --- Beat 4.3 — the honest statement ------------------------------------------------------
        with self.beat("4.3", extend=1.5) as b:
            b.wait_until("general")
            eq_gen = st.place_eq(self.eq("general", terms=GEN_TERMS, roles=roles_for(GEN_TERMS)))
            self.play(morph(eq_ols, eq_gen),
                      run_time=P.RUN_TIME)
            self.play(Indicate(real_slice, color=P.CONCEPT, scale_factor=1.05), run_time=P.RUN_TIME)
            self.play(Indicate(line, color=P.MODEL, scale_factor=1.02), run_time=P.RUN_TIME)
