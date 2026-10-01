import numpy as np
import pytest
from manim import Axes

from dsanim import palette as P
from dsanim.components.conditional import band, conditional_fit, conditional_slice, mean_point
from dsanim.components.gaussian import INFLECTION, GaussianSlice
from dsanim.components.scatter import Scatter


@pytest.fixture
def axes():
    return Axes(x_range=[0, 10, 1], y_range=[0, 20, 5], x_length=8, y_length=6)


def test_slice_peak_sits_at_mu_and_bulges_peak_width(axes):
    g = GaussianSlice(axes, x0=2, mu=10, sigma=2, peak_width=1.5)
    base = axes.c2p(2, 10)
    assert g.peak_point() == pytest.approx(base + np.array([1.5, 0, 0]))
    assert axes.p2c(g.peak_point())[1] == pytest.approx(10)


def test_slice_side_flips_direction(axes):
    right = GaussianSlice(axes, 5, 10, 2, peak_width=1.0, side=1)
    left = GaussianSlice(axes, 5, 10, 2, peak_width=1.0, side=-1)
    assert right.peak_point()[0] > axes.c2p(5, 10)[0] > left.peak_point()[0]


def test_slice_width_at_sigma_is_inflection(axes):
    g = GaussianSlice(axes, 2, 10, 2, peak_width=1.0)
    assert g.width_at(12) == pytest.approx(INFLECTION)
    seg = g.sigma_segment()
    assert axes.p2c(seg.get_start())[1] == pytest.approx(10)
    assert axes.p2c(seg.get_end())[1] == pytest.approx(12)


def test_slice_is_clipped_to_axes_y_range(axes):
    g = GaussianSlice(axes, 2, mu=1, sigma=3)  # would extend below y=0
    ys = [axes.p2c(p)[1] for p in g.curve_points]
    assert min(ys) >= -1e-9 and max(ys) <= 20 + 1e-9


@pytest.mark.parametrize("kw", [{"sigma": 0}, {"sigma": -1}, {"side": 0}])
def test_slice_rejects_bad_parameters(axes, kw):
    args = dict(x0=2, mu=10, sigma=2) | kw
    with pytest.raises(ValueError):
        GaussianSlice(axes, **args)


def test_slice_default_colour_is_concept(axes):
    g = GaussianSlice(axes, 2, 10, 2)
    assert g.curve.get_stroke_color().to_hex().upper() == P.CONCEPT.upper()


def test_scatter_positions_follow_data(axes):
    s = Scatter(axes, [1, 2, 3], [4, 5, 6])
    assert len(s) == 3
    assert s[1].get_center() == pytest.approx(axes.c2p(2, 5))


def test_scatter_collapse_keeps_y_and_leaves_original(axes):
    s = Scatter(axes, [1, 2, 3], [4, 5, 6])
    c = s.collapsed(0)
    assert [axes.p2c(d.get_center())[0] for d in c] == pytest.approx([0, 0, 0])
    assert [axes.p2c(d.get_center())[1] for d in c] == pytest.approx([4, 5, 6])
    assert s[2].get_center() == pytest.approx(axes.c2p(3, 6))


def test_scatter_rejects_mismatched_lengths(axes):
    with pytest.raises(ValueError):
        Scatter(axes, [1, 2], [1])


def test_scatter_focus_band(axes):
    s = Scatter(axes, [1, 2, 3], [4, 5, 6]).focus_band(2, 0.5)
    assert [d.get_fill_opacity() for d in s] == pytest.approx([P.FADED_OPACITY, 1, P.FADED_OPACITY])
    assert s[1].get_fill_color().to_hex().upper() == P.DATA_FOCUS.upper()
    s.unfocus()
    assert all(d.get_fill_opacity() == pytest.approx(1) for d in s)


def test_band_spans_width_and_full_height(axes):
    b = band(axes, 5, 1)
    assert b.width == pytest.approx(abs(axes.c2p(6, 0)[0] - axes.c2p(4, 0)[0]))
    assert b.height == pytest.approx(6)
    assert b.get_center()[0] == pytest.approx(axes.c2p(5, 0)[0])


def test_conditional_slice_uses_band_points(axes):
    xs = np.array([1.0, 1.1, 0.9, 8.0])
    ys = np.array([5.0, 7.0, 6.0, 19.0])
    fit = conditional_fit(xs, ys, 1.0, 0.5)
    g = conditional_slice(axes, xs, ys, 1.0, 0.5, side=-1)
    assert g.mu == pytest.approx(fit.mean) and g.sigma == pytest.approx(fit.sd)
    assert axes.p2c(mean_point(axes, xs, ys, 1.0, 0.5))[1] == pytest.approx(fit.mean)


def test_band_y_span(axes):
    b = band(axes, 5, 1, y_span=(2, 18))
    assert b.height == pytest.approx(abs(axes.c2p(0, 18)[1] - axes.c2p(0, 2)[1]))
    assert b.get_bottom()[1] == pytest.approx(axes.c2p(0, 2)[1])
    with pytest.raises(ValueError):
        band(axes, 5, 1, y_span=(18, 2))


def test_slice_set_params_moves_in_place(axes):
    g = GaussianSlice(axes, x0=2, mu=10, sigma=2, peak_width=1.0)
    same = g.set_params(x0=5, mu=12, sigma=1)
    assert same is g
    assert g.peak_point() == pytest.approx(axes.c2p(5, 12) + np.array([1.0, 0, 0]))
    assert g.mean_line().get_start() == pytest.approx(axes.c2p(5, 12))
    assert g.width_at(13) == pytest.approx(INFLECTION)
    with pytest.raises(ValueError):
        g.set_params(sigma=0)


def test_conditional_slice_floors_sigma_for_identical_values(axes):
    from dsanim.components.conditional import SIGMA_FLOOR
    g = conditional_slice(axes, [1.0, 1.1, 0.9], [5.0, 5.0, 5.0], 1.0, 0.5)
    assert g.sigma == pytest.approx(SIGMA_FLOOR * 20)


def test_slice_appear_is_one_animation(axes):
    from manim import AnimationGroup
    assert isinstance(GaussianSlice(axes, 2, 10, 2).appear(), AnimationGroup)


def test_slice_appear_adds_the_slice_itself_to_the_scene(axes):
    """Regression: an AnimationGroup without group=self left the slice outside the scene,
    so updaters attached to it never ran (sample video, Scene 4)."""
    g = GaussianSlice(axes, 2, 10, 2)
    assert g.appear().mobject is g
