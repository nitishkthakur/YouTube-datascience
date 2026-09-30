import numpy as np
import pytest

from dsanim import data, stats


def test_normal_fit_is_mle():
    fit = stats.normal_fit([1.0, 2.0, 3.0, 4.0])
    assert fit.mean == 2.5 and fit.n == 4
    assert fit.sd == pytest.approx(np.std([1, 2, 3, 4], ddof=0))


def test_normal_fit_rejects_empty():
    with pytest.raises(ValueError):
        stats.normal_fit([])


def test_band_weights_shape():
    w = stats.band_weights([0.0, 0.5, 1.0, 2.0], x0=0.0, half_width=1.0)
    assert w.tolist() == pytest.approx([1.0, 0.75, 0.0, 0.0])


def test_band_weights_rejects_bad_width():
    with pytest.raises(ValueError):
        stats.band_weights([0.0], 0.0, 0.0)


def test_local_normal_only_uses_points_in_band():
    x = np.array([0.0, 0.1, -0.1, 5.0])
    y = np.array([1.0, 1.0, 1.0, 100.0])
    fit = stats.local_normal(x, y, x0=0.0, half_width=1.0)
    assert fit.mean == pytest.approx(1.0) and fit.sd == pytest.approx(0.0) and fit.n == 3


def test_local_normal_empty_band_raises():
    with pytest.raises(ValueError):
        stats.local_normal([0.0], [1.0], x0=10.0, half_width=1.0)


def test_local_normal_recovers_linear_gaussian_truth():
    x, y = data.linear_gaussian(n=20000, seed=3)
    fit = stats.local_normal(x, y, x0=3.0, half_width=0.3)
    assert fit.mean == pytest.approx(2.0 + 0.5 * 3.0, abs=0.05)
    assert fit.sd == pytest.approx(0.6, abs=0.05)


def test_local_normal_is_continuous_as_band_slides():
    df = data.auto_mpg()
    xs = np.linspace(900, 2200, 400)
    means = [stats.local_normal(df.weight_kg, df.mpg, v, 75).mean for v in xs]
    assert np.max(np.abs(np.diff(means))) < 0.5  # no jumps as points enter/leave


def test_in_band_mask():
    assert stats.in_band([0.0, 0.99, 1.0], 0.0, 1.0).tolist() == [True, True, False]
