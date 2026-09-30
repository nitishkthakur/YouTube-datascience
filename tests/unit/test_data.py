import numpy as np
import pytest

from dsanim import data


def test_auto_mpg_matches_documented_provenance():
    df = data.auto_mpg()
    assert len(df) == 398
    assert df["horsepower"].isna().sum() == 6
    assert df["weight_kg"].min() == pytest.approx(731.6, abs=1)
    assert df["weight_kg"].max() == pytest.approx(2331.4, abs=1)
    assert df["model_year"].between(1970, 1982).all()
    assert set(df["origin"]) == {"usa", "europe", "japan"}


def test_fuel_economy_curated_subset():
    df = data.fuel_economy()
    assert (df["year"] >= 2020).all()
    assert df[["displ", "comb08"]].notna().all().all()
    assert df["fuelType1"].str.contains("Gasoline").all()
    assert len(df) > 1000


def test_sample_is_reproducible():
    df = data.auto_mpg()
    assert data.sample(df, 60, seed=3).index.equals(data.sample(df, 60, seed=3).index)


def test_linear_gaussian_is_seeded_and_follows_its_docstring():
    x1, y1 = data.linear_gaussian(n=2000, seed=1)
    x2, y2 = data.linear_gaussian(n=2000, seed=1)
    assert np.array_equal(y1, y2)
    slope, intercept = np.polyfit(x1, y1, 1)
    assert slope == pytest.approx(0.5, abs=0.05) and intercept == pytest.approx(2.0, abs=0.1)
    assert np.std(y1 - (intercept + slope * x1)) == pytest.approx(0.6, abs=0.05)
