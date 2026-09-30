"""Text and equation factories, plus the XeLaTeX template that sets math in STIX Two.

Scenes never call `Text(...)` / `MathTex(...)` with styling arguments directly; they call
`text()` / `label()` here, and get equations through `DSScene.eq(<id>)` so every on-screen
equation is the exact LaTeX frozen in script.md.
"""

from __future__ import annotations

from manim import MathTex, TexTemplate, Text

from dsanim import layout, palette as P


def scaled(size: float) -> float:
    """Apply the Shorts text scale when rendering vertically (AGENTS.md §10)."""
    return size * P.VERTICAL_TEXT_SCALE if layout.is_vertical() else size


def tex_template() -> TexTemplate:
    """XeLaTeX + unicode-math, STIX Two Math for math and STIX Two Text for \\text{}."""
    return TexTemplate(
        tex_compiler="xelatex",
        output_format=".xdv",
        documentclass=r"\documentclass[preview]{standalone}",
        preamble="\n".join(
            [
                r"\usepackage{amsmath}",
                r"\usepackage{unicode-math}",
                rf"\setmainfont{{{P.FONT_MATH_TEXT}}}",
                rf"\setmathfont{{{P.FONT_MATH}}}",
            ]
        ),
    )


def text(s: str, size: int = P.SIZE_BODY, color: str = P.TEXT, **kw) -> Text:
    return Text(s, font=P.FONT_TEXT, font_size=scaled(size), color=color, **kw)


def label(s: str, color: str = P.TEXT, **kw) -> Text:
    return text(s, size=P.SIZE_LABEL, color=color, **kw)


def code(s: str, size: int = P.SIZE_LABEL, color: str = P.TEXT, **kw) -> Text:
    return Text(s, font=P.FONT_CODE, font_size=scaled(size), color=color, **kw)


# Single symbols that may label diagrams without being "equations" (AGENTS.md §9 governs
# equations). Anything longer than one symbol belongs in script.md and comes via self.eq().
SYMBOLS = {
    "mu": r"\mu", "sigma": r"\sigma", "x": "x", "y": "y", "X": "X", "Y": "Y",
    "beta0": r"\beta_0", "beta1": r"\beta_1", "epsilon": r"\varepsilon",
    "mu(x)": r"\mu(x)", "sigma(x)": r"\sigma(x)",
}


def symbol(name: str, size: int = P.SIZE_EQUATION, color: str = P.TEXT, **kw) -> MathTex:
    """A single math symbol for labelling a diagram (e.g. symbol("mu"))."""
    if name not in SYMBOLS:
        raise KeyError(f"unknown symbol {name!r}; allowed: {sorted(SYMBOLS)}")
    return math(SYMBOLS[name], size=size, color=color, **kw)


def math(*tex_strings: str, size: int = P.SIZE_EQUATION, color: str = P.TEXT, **kw) -> MathTex:
    """Low-level MathTex factory. In topic scenes use DSScene.eq(<id>) instead (lint-enforced)."""
    return MathTex(*tex_strings, font_size=scaled(size), color=color, **kw)
