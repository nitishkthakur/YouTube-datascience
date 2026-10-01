import pytest
from manim import config

from dsanim import layout
from dsanim.components.chart import ChartSpec, build_chart, equation_panel, peak_room, place_equation
from dsanim.typography import math

SPEC = ChartSpec((500, 2500, 500), (0, 50, 10), (1000, 1500, 2000), (10, 20, 30, 40, 50), "weight (kg)", "mpg")


@pytest.fixture
def restore_config():
    saved = (config.frame_width, config.frame_height, config.pixel_width, config.pixel_height)
    yield
    config.frame_width, config.frame_height, config.pixel_width, config.pixel_height = saved


@pytest.mark.parametrize("vertical", [False, True])
def test_chart_fits_the_plot_region(vertical, restore_config):
    layout.apply_orientation(vertical)
    L = layout.regions(vertical)
    chart = build_chart(L, SPEC)
    assert L.plot.contains(chart.group, tol=1e-3)
    assert len(chart.group) == 5   # axes, x nums, y nums, x title, y title


def test_equation_panel_is_inside_the_equation_region(restore_config):
    layout.apply_orientation(False)
    L = layout.regions(False)
    eq, ledger = equation_panel(L)
    assert eq.top <= L.equation.top + 1e-9 and ledger.bottom >= L.equation.bottom - 1e-9
    assert eq.bottom > ledger.top


@pytest.mark.slow
def test_place_equation_scales_up_to_the_cap_and_never_clips(restore_config):
    layout.apply_orientation(False)
    L = layout.regions(False)
    eq_region, _ = equation_panel(L)
    small = place_equation(math("x"), eq_region)
    assert small.width == pytest.approx(math("x").width * 1.3, rel=0.05)
    long = place_equation(math(r"Y = \beta_0 + \beta_1 x + \varepsilon, \qquad \varepsilon \sim \mathcal{N}(0, \sigma^2)"), eq_region)
    assert eq_region.contains(long, tol=1e-3)


@pytest.mark.parametrize("vertical,expect_full", [(False, True), (True, False)])
def test_peak_room_shrinks_only_in_the_narrow_frame(vertical, expect_full, restore_config):
    layout.apply_orientation(vertical)
    L = layout.regions(vertical)
    chart = build_chart(L, SPEC)
    room = peak_room(L, chart.axes, 2275, 1.3)
    assert (room == 1.3) == expect_full
    assert 0.2 <= room <= 1.3
