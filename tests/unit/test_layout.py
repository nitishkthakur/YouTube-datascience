import pytest
from manim import Square, config

from dsanim import layout


@pytest.fixture
def restore_config():
    saved = (config.frame_width, config.frame_height, config.pixel_width, config.pixel_height)
    yield
    config.frame_width, config.frame_height, config.pixel_width, config.pixel_height = saved


@pytest.mark.parametrize("vertical", [False, True])
def test_orientation_sets_frame_and_pixels(vertical, restore_config):
    layout.apply_orientation(vertical)
    assert config.frame_width == pytest.approx(8.0 if vertical else 16 / 9 * 8)
    assert config.frame_height == pytest.approx(16 / 9 * 8 if vertical else 8.0)
    portrait = config.pixel_height > config.pixel_width
    assert portrait == vertical
    # same pixels-per-unit in both orientations
    assert config.pixel_width / config.frame_width == pytest.approx(
        config.pixel_height / config.frame_height, rel=1e-3)


def test_orientation_from_env(monkeypatch, restore_config):
    monkeypatch.setenv("DSANIM_VERTICAL", "1")
    assert layout.is_vertical()
    layout.apply_orientation()
    assert config.frame_height > config.frame_width


@pytest.mark.parametrize("vertical", [False, True])
def test_safe_area_is_five_percent_inset(vertical, restore_config):
    layout.apply_orientation(vertical)
    f, s = layout.frame(), layout.safe()
    assert s.width == pytest.approx(0.9 * f.width)
    assert s.height == pytest.approx(0.9 * f.height)
    assert s.left - f.left == pytest.approx(0.05 * f.width)


@pytest.mark.parametrize("vertical", [False, True])
def test_regions_lie_inside_safe_area_and_do_not_overlap(vertical, restore_config):
    layout.apply_orientation(vertical)
    L = layout.regions(vertical)
    boxes = [r for r in (L.plot, L.equation, L.caption) if r is not None]
    for r in boxes:
        assert r.left >= L.safe.left - 1e-9 and r.right <= L.safe.right + 1e-9
        assert r.bottom >= L.safe.bottom - 1e-9 and r.top <= L.safe.top + 1e-9
    for a in boxes:
        for b in boxes:
            if a is not b:
                overlap_x = min(a.right, b.right) - max(a.left, b.left)
                overlap_y = min(a.top, b.top) - max(a.bottom, b.bottom)
                assert overlap_x <= 1e-9 or overlap_y <= 1e-9, (a.name, b.name)


def test_landscape_split_is_60_40(restore_config):
    layout.apply_orientation(False)
    L = layout.regions(False)
    assert L.caption is None
    total = L.plot.width + L.equation.width
    assert L.plot.width / total == pytest.approx(0.6, abs=0.02)
    assert L.plot.center[0] < L.equation.center[0]


def test_vertical_split_is_60_30_10(restore_config):
    layout.apply_orientation(True)
    L = layout.regions(True)
    total = L.plot.height + L.equation.height + L.caption.height
    assert L.plot.height / total == pytest.approx(0.6, abs=0.02)
    assert L.equation.height / total == pytest.approx(0.3, abs=0.02)
    assert L.plot.center[1] > L.equation.center[1] > L.caption.center[1]


def test_fit_scales_down_and_centres(restore_config):
    layout.apply_orientation(False)
    r = layout.Region("r", -1, 1, -1, 1)
    sq = Square(side_length=10)
    r.fit(sq)
    assert r.contains(sq)
    assert sq.get_center() == pytest.approx(r.center)


def test_fit_does_not_scale_up_by_default():
    r = layout.Region("r", -5, 5, -5, 5)
    sq = Square(side_length=1)
    r.fit(sq)
    assert sq.width == pytest.approx(1)
    r.fit(sq, scale_up=True)
    assert sq.width == pytest.approx(10)


def test_contains_detects_overflow():
    r = layout.Region("r", -1, 1, -1, 1)
    assert not r.contains(Square(side_length=3))
