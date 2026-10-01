"""Equation helpers: reveal terms one at a time and morph one equation into the next.

AGENTS.md §4: equations appear one term at a time when the narration introduces them, and a
morph must keep the terms that survive in place. Both need the equation split into terms:
`DSScene.eq(id, terms=[...], roles={...})` (see typography.math).

    eq = self.eq("conditional", terms=[...], roles={r"\\mu(x)": P.MODEL})
    hide(eq, [r"\\mu(x)"])            # add eq with that term invisible
    self.play(reveal(eq, [r"\\mu(x)"]), run_time=b.until("mean"))
    self.play(morph(eq_old, eq_new))
"""

from __future__ import annotations

from manim import AnimationGroup, MathTex, TransformMatchingTex, VGroup

from dsanim import palette as P


def roles_for(terms: list[str], roles: dict[str, str]) -> dict[str, str]:
    """The subset of a tier's role map that applies to one equation's terms."""
    return {t: roles[t] for t in terms if t in roles}


def parts(eq: MathTex, terms: list[str]) -> list[VGroup]:
    found = []
    for t in terms:
        part = eq.get_part_by_tex(t)
        if part is None:
            raise ValueError(f"{t!r} is not a term or isolated substring of {eq.tex_string!r}; "
                             "pass it in terms=/roles= when building the equation")
        found.append(part)
    return found


def hide(eq: MathTex, terms: list[str]) -> MathTex:
    """Make the given terms invisible (before adding eq to the scene) so reveal() can fade them in."""
    for part in parts(eq, terms):
        part.set_opacity(0.0)
    return eq


def reveal(eq: MathTex, terms: list[str], run_time: float = P.ENTRANCE_TIME) -> AnimationGroup:
    """Fade the given (hidden) terms in, in place."""
    return AnimationGroup(*[part.animate.set_opacity(1.0) for part in parts(eq, terms)],
                          run_time=run_time)


def morph(old: MathTex, new: MathTex, run_time: float = P.RUN_TIME) -> TransformMatchingTex:
    """Old -> new, matching top-level terms by their tex.

    Surviving terms slide to their new places; removed terms fade out towards where the new
    terms appear; new terms fade in. Nothing morphs glyph-by-glyph, so no half-formed symbols
    mid-transition. Build both equations with terms=[...] so shared terms are identical strings.
    (Manim 0.21's key_map uses FadeTransformPieces, which requires equal glyph counts and
    raises otherwise — so renames are deliberately not supported here.)
    """
    return TransformMatchingTex(old, new, transform_mismatches=False,
                                fade_transform_mismatches=False, run_time=run_time)
