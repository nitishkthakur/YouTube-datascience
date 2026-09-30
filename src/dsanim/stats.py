"""Small, explicit estimators used on screen. Every number an animation draws from data comes
from a function here (or data.py), so the video can state exactly how it was computed.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class NormalFit:
    mean: float
    sd: float
    n: int  # observations that carry weight


def normal_fit(y) -> NormalFit:
    """Maximum-likelihood Normal fit: sample mean and sd with ddof=0 (the MLE of sigma)."""
    y = np.asarray(y, dtype=float)
    if y.size == 0:
        raise ValueError("normal_fit needs at least one value")
    return NormalFit(float(y.mean()), float(y.std(ddof=0)), int(y.size))


def band_weights(x, x0: float, half_width: float) -> np.ndarray:
    """Epanechnikov weights: 1 - ((x - x0)/h)^2 inside the band |x - x0| < h, 0 outside.

    Only points visibly inside the band get weight, and the weights fall to zero at the band
    edges, so estimates change continuously as the band slides (no jumps as points enter).
    """
    if half_width <= 0:
        raise ValueError("half_width must be > 0")
    u = (np.asarray(x, dtype=float) - x0) / half_width
    return np.clip(1.0 - u**2, 0.0, None)


def local_normal(x, y, x0: float, half_width: float) -> NormalFit:
    """Normal fit to the y values of points in the band around x0 (weighted MLE).

    mean = sum(w*y)/sum(w);  sd = sqrt(sum(w*(y-mean)^2)/sum(w)), w = band_weights(...).
    This is a local (kernel) estimate of mu(x) and sigma(x): no straight-line assumption.
    """
    y = np.asarray(y, dtype=float)
    w = band_weights(x, x0, half_width)
    total = w.sum()
    if total <= 0:
        raise ValueError(f"no points within {half_width} of x0={x0}")
    mean = float((w * y).sum() / total)
    sd = float(np.sqrt((w * (y - mean) ** 2).sum() / total))
    return NormalFit(mean, sd, int((w > 0).sum()))


def in_band(x, x0: float, half_width: float) -> np.ndarray:
    """Boolean mask of points inside the band (what the viewer sees highlighted)."""
    return np.abs(np.asarray(x, dtype=float) - x0) < half_width
