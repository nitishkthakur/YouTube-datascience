"""Scene 1 — "A line through the cloud". Spec: ../shotlist.md."""

from manim import Create, FadeIn, Indicate, Write

from common.stage import LINE_TERMS, build_stage, roles_for
from dsanim import palette as P
from dsanim.scene import DSScene


class Scene01(DSScene):
    def construct(self):
        st = build_stage(self)

        # --- Beat 1.1 — the cloud ----------------------------------------------------------
        with self.beat("1.1", extend=1.0) as b:
            self.play(FadeIn(st.chart), run_time=P.ENTRANCE_TIME)
            b.wait_until("cars")
            self.play(FadeIn(st.scatter), run_time=1.5)

        # --- Beat 1.2 — the line and its equation ------------------------------------------
        with self.beat("1.2", extend=1.0) as b:
            b.wait_until("line")
            line = st.line()
            self.play(Create(line), run_time=1.2)
            eq = st.place_eq(self.eq("line", terms=LINE_TERMS, roles=roles_for(LINE_TERMS)))
            self.play(Write(eq), run_time=P.RUN_TIME)

        # --- Beat 1.3 — what does it claim? -------------------------------------------------
        with self.beat("1.3", extend=0.5) as b:
            self.play(Indicate(line, color=P.MODEL, scale_factor=1.02), run_time=P.RUN_TIME)
