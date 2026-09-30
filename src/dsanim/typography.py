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
    "mu(x)": r"\mu(x)", "sigma(x)": r"\sigma(x)", "n": "n", "N": "N", "k": "k",
    "hat y": r"\hat{y}", "E[Y|X=x]": r"\mathbb{E}[Y \mid X = x]",
}


def symbol(name: str, size: int = P.SIZE_EQUATION, color: str = P.TEXT, **kw) -> MathTex:
    """A single math symbol for labelling a diagram (e.g. symbol("mu"))."""
    if name not in SYMBOLS:
        raise KeyError(f"unknown symbol {name!r}; allowed: {sorted(SYMBOLS)}")
    return math(SYMBOLS[name], size=size, color=color, **kw)


def _squash(s: str) -> str:
    return "".join(s.split())


class TermsMismatch(ValueError):
    pass


def math(latex: str, *, terms: list[str] | None = None, roles: dict[str, str] | None = None,
         size: int = P.SIZE_EQUATION, color: str = P.TEXT, **kw) -> MathTex:
    """Low-level MathTex factory. In topic scenes use DSScene.eq(<id>) instead (lint-enforced).

    terms: an ordered split of `latex` into the pieces that move independently in a morph
      (TransformMatchingTex matches top-level parts by their tex). They must concatenate back
      to `latex` (whitespace-insensitive) — so the equation on screen is still exactly the
      script's, just tokenised — or TermsMismatch is raised.
    roles: LaTeX substrings -> colours, e.g. {r"\\mu(x)": P.MODEL, "X=x": P.PARAM}. A role
      key that is not one of the terms is isolated as a sub-part; either way it can be
      coloured, hidden and revealed (components/equations.py).
    """
    roles = roles or {}
    if terms:
        if _squash("".join(terms)) != _squash(latex):
            raise TermsMismatch(f"terms {terms} do not concatenate to {latex!r}")
        extra = [r for r in roles if r not in terms]
        eq = MathTex(*terms, substrings_to_isolate=extra or None,
                     font_size=scaled(size), color=color, **kw)
    else:
        eq = MathTex(latex, substrings_to_isolate=list(roles) or None,
                     font_size=scaled(size), color=color, **kw)
    for substring, role_color in roles.items():
        if eq.get_part_by_tex(substring) is None:
            raise TermsMismatch(f"role {substring!r} not found in {latex!r}")
        eq.set_color_by_tex(substring, role_color)
    return eq
