"""Download the channel's real datasets from their official sources and write the curated,
committed copies under data/. Re-run to refresh; raw downloads go to data/cache/ (ignored).

    uv run python tools/fetch_data.py            # all
    uv run python tools/fetch_data.py auto_mpg   # one

Provenance and licences: data/PROVENANCE.md. Update it whenever this script changes.
"""

from __future__ import annotations

import sys
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "cache"

SOURCES = {
    "auto_mpg": "https://archive.ics.uci.edu/static/public/9/auto+mpg.zip",
    "fuel_economy": "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip",
}


def download(name: str) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    dest = CACHE / f"{name}.zip"
    print(f"downloading {SOURCES[name]}")
    urllib.request.urlretrieve(SOURCES[name], dest)
    return dest


def auto_mpg() -> None:
    out = ROOT / "data" / "auto_mpg"
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(download("auto_mpg")) as z:
        (out / "auto-mpg.data").write_bytes(z.read("auto-mpg.data"))
        (out / "auto-mpg.names").write_bytes(z.read("auto-mpg.names"))
    print(f"wrote {out}/auto-mpg.data")


def fuel_economy(min_year: int = 2020) -> None:
    out = ROOT / "data" / "fuel_economy"
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(download("fuel_economy")) as z:
        with z.open("vehicles.csv") as f:
            df = pd.read_csv(f, low_memory=False)
    keep = ["id", "year", "make", "model", "VClass", "drive", "trany", "cylinders", "displ",
            "fuelType1", "city08", "highway08", "comb08", "co2TailpipeGpm"]
    conventional = df["atvType"].isna()  # excludes Hybrid, EV, Plug-in Hybrid, FFV, Diesel, CNG
    gasoline = df["fuelType1"].isin(["Regular Gasoline", "Premium Gasoline", "Midgrade Gasoline"])
    cur = df.loc[conventional & gasoline & (df["year"] >= min_year), keep]
    cur = cur.dropna(subset=["displ", "comb08"]).sort_values(["year", "make", "model", "id"])
    path = out / f"vehicles_{min_year}plus_gasoline.csv"
    cur.to_csv(path, index=False)
    (out / "FETCHED").write_text(f"{date.today().isoformat()}\n{SOURCES['fuel_economy']}\n")
    print(f"wrote {path} ({len(cur)} rows, years {cur.year.min()}-{cur.year.max()})")


if __name__ == "__main__":
    wanted = sys.argv[1:] or list(SOURCES)
    for name in wanted:
        globals()[name]()
