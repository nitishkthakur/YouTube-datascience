"""Ledger, equation helpers, dot-histogram collapse, equation terms/roles."""

import numpy as np
import pytest
from manim import Axes, TransformMatchingTex

import dsanim.scene  # noqa: F401  (XeLaTeX template)
from dsanim import layout, palette as P, typography as T
from dsanim.components.equations import hide, morph, parts, reveal
from dsanim.components.ledger import Ledger
from dsanim.components.scatter import Scatter

COND = r"Y \mid X=x \sim \mathcal{N}(\mu(x), \sigma(x)^2)"
COND_TERMS = ["Y", r"\mid X=x", r"\sim", r"\mathcal{N}(", r"\mu", "(x)", ",", r"\sigma", "(x)", "^2)"]
MARG = r"Y \sim \mathcal{N}(\mu, \sigma^2)"
MARG_TERMS = ["Y", r"\sim", r"\mathcal{N}(", r"\mu", ",", r"\sigma", "^2)"]


@pytest.fixture
def axes():
    return Axes(x_range=[0, 10, 1], y_range=[0, 20, 5], x_length=8, y_length=6)


def test_collapsed_histogram_stacks_within_bins(axes):
    s = Scatter(axes, [1, 2, 3, 4], [4.0, 4.4, 4.9, 12.0])
    h = s.collapsed_histogram(x_value=0, bin_width=1.0, side=1)
    xs = [h[i].get_center()[0] for i in range(4)]
    ys = [axes.p2c(h[i].get_center())[1] for i in range(4)]
    base = axes.c2p(0, 4.5)[0]
    assert ys[:3] == pytest.approx([4.5, 4.5, 4.5]) and ys[3] == pytest.approx(12.5)
    assert xs[0] < xs[1] < xs[2] and xs[0] > base            # three in the same bin, stacked right
    assert xs[3] == pytest.approx(xs[0])                        # first in its bin sits nearest the axis
    with pytest.raises(ValueError):
        s.collapsed_histogram(0, 0)


@pytest.mark.slow
def test_math_roles_colour_substrings():
    eq = T.math(COND, roles={r"\mu(x)": P.MODEL, "X=x": P.PARAM})
    assert eq.get_part_by_tex(r"\mu(x)").get_color().to_hex().upper() == P.MODEL.upper()
    assert eq.get_part_by_tex("X=x").get_color().to_hex().upper() == P.PARAM.upper()
    assert T._squash(eq.tex_string) == T._squash(COND)


@pytest.mark.slow
def test_math_terms_must_concatenate_to_the_script_latex():
    eq = T.math(COND, terms=COND_TERMS, roles={r"\mu": P.MODEL})
    assert [p.tex_string for p in eq.submobjects] == COND_TERMS
    with pytest.raises(T.TermsMismatch):
        T.math(COND, terms=["Y", r"\sim"])
    with pytest.raises(T.TermsMismatch):
        T.math(COND, roles={"nope": P.MODEL})


@pytest.mark.slow
def test_hide_and_reveal_terms():
    eq = T.math(COND, terms=COND_TERMS)
    hide(eq, ["(x)"])
    assert all(p.get_fill_opacity() == 0 for p in parts(eq, ["(x)"]))
    assert len(reveal(eq, ["(x)"]).animations) == 1
    with pytest.raises(ValueError):
        reveal(eq, ["zzz"])


@pytest.mark.slow
def test_morph_is_term_matching_not_glyph_matching():
    old = T.math(MARG, terms=MARG_TERMS)
    new = T.math(COND, terms=COND_TERMS)
    anim = morph(old, new)
    assert isinstance(anim, TransformMatchingTex)
    shared = {p.tex_string for p in old.submobjects} & {p.tex_string for p in new.submobjects}
    assert shared == {"Y", r"\sim", r"\mathcal{N}(", r"\mu", ",", r"\sigma", "^2)"}


@pytest.mark.slow
def test_ledger_rows_refresh_from_getters():
    state = {"x": 1500.0, "mu": 19.7}
    rows = [("x", lambda: state["x"], {"decimals": 0, "unit": "kg", "color": P.PARAM}),
            ("mu(x)", lambda: state["mu"], {"decimals": 1, "color": P.MODEL})]
    region = layout.Region("r", -3, 3, -2, 2)
    ledger = Ledger(rows, region=region)
    assert len(ledger) == 2 and region.contains(ledger)
    state["x"], state["mu"] = 2200.0, 11.9
    ledger.refresh()
    assert ledger._getters[0][0].get_value() == pytest.approx(2200)
    assert ledger._getters[1][0].get_value() == pytest.approx(11.9)


@pytest.mark.slow
def test_ledger_live_adds_time_based_updater():
    ledger = Ledger([("n", lambda: 45, {"decimals": 0})]).live()
    assert ledger.has_time_based_updater()
