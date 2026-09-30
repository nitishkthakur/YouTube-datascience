"""Gallery: the channel style sheet — palette roles, type, an equation, layout regions.

Render:  uv run python tools/render.py gallery/style_sheet.py StyleSheet -q m --sheet
         (add --vertical for the 9:16 layout)
This is the first thing to look at after any change to palette.py, layout.py or typography.py.
"""

from manim import (DOWN, RIGHT, Axes, Create, DashedVMobject, Dot, FadeIn, FadeOut,
                   LaggedStart, Rectangle, Square, VGroup, Write)

from dsanim import data, palette as P, typography as T
from dsanim.scene import DSScene

ROLES = [("DATA", P.DATA), ("DATA_FOCUS", P.DATA_FOCUS), ("CONCEPT", P.CONCEPT),
         ("PARAM", P.PARAM), ("MODEL", P.MODEL), ("ERROR", P.ERROR)]


def region_outline(region):
    box = Rectangle(width=region.width, height=region.height, stroke_color=P.MUTED,
                    stroke_width=1).move_to(region.center)
    return DashedVMobject(box, num_dashes=60)


class StyleSheet(DSScene):
    def construct(self):
        L = self.layout

        # --- Beat 1.1: colour roles ------------------------------------------------------
        with self.beat("1.1") as b:
            title = T.text("Colour roles", size=P.SIZE_TITLE)
            swatches = VGroup(*[
                VGroup(Square(0.7, fill_color=c, fill_opacity=1, stroke_width=0),
                       T.label(name)).arrange(RIGHT, buff=0.3)
                for name, c in ROLES
            ]).arrange_in_grid(cols=1 if self.vertical else 2, buff=(1.0, 0.45),
                               col_alignments="ll" if not self.vertical else "l")
            page = VGroup(title, swatches).arrange(DOWN, buff=0.7)
            L.safe.fit(page)
            self.play(FadeIn(title, shift=0.2 * DOWN), run_time=P.ENTRANCE_TIME)
            b.wait_until("swatches")
            self.play(LaggedStart(*[FadeIn(s) for s in swatches], lag_ratio=0.15),
                      run_time=min(2.0, b.remaining))
        self.play(FadeOut(page), run_time=P.ENTRANCE_TIME)

        # --- Beat 1.2: plot region + equation region ---------------------------------------
        with self.beat("1.2") as b:
            outlines = VGroup(*[region_outline(r) for r in (L.plot, L.equation)])
            axes = Axes(x_range=[0, 6, 1], y_range=[0, 6, 1],
                        x_length=L.plot.width * 0.9, y_length=L.plot.height * 0.9,
                        axis_config={"color": P.MUTED, "stroke_width": 2}).move_to(L.plot.center)
            x, y = data.linear_gaussian()
            dots = VGroup(*[Dot(axes.c2p(xi, yi), radius=0.05, color=P.DATA) for xi, yi in zip(x, y)])
            line = axes.plot(lambda t: 2.0 + 0.5 * t, x_range=[0, 6], color=P.MODEL, stroke_width=5)
            eq = self.eq("style-model")
            L.equation.fit(eq, pad=0.2)
            self.play(Create(outlines), Create(axes), run_time=P.RUN_TIME)
            self.play(FadeIn(dots), run_time=P.ENTRANCE_TIME)
            b.wait_until("model")
            self.play(Create(line), Write(eq), run_time=min(1.5, b.remaining))
