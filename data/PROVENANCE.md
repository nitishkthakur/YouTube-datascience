# Data provenance

Every real dataset shown on screen, with its source, licence and the exact citation to use
in video descriptions and articles. Curated copies are committed; raw downloads go to
`data/cache/` (git-ignored). Refresh with `uv run python tools/fetch_data.py`.

## auto_mpg/ — UCI Auto MPG
- Source: https://archive.ics.uci.edu/dataset/9/auto+mpg (zip: https://archive.ics.uci.edu/static/public/9/auto+mpg.zip)
- Licence: **CC BY 4.0** (attribution required).
- Cite: Quinlan, R. (1993). Auto MPG [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5859H
- Contents: 398 cars, model years 1970–82. `horsepower` missing ("?") in 6 rows.
  Weight is in lb in the source (1,613–5,140 lb ≈ 732–2,331 kg); `dsanim.data.auto_mpg()`
  adds `weight_kg` = lb × 0.45359237.
- Note: seaborn's `mpg` is a copy of this data via a third-party mirror — cite UCI, not seaborn.
  R's `mtcars` (32 cars) and ggplot2's `mpg` (234 cars, no weight) are different datasets.

## fuel_economy/ — US DOE/EPA fuel economy data
- Source: https://www.fueleconomy.gov/feg/download.shtml (zip: https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip)
- Licence: US federal government work — **public domain** (credit anyway).
- Cite: U.S. Department of Energy & U.S. Environmental Protection Agency, fueleconomy.gov vehicle data, accessed <date in fuel_economy/FETCHED>.
- Curated subset `vehicles_2020plus_gasoline.csv`: model years ≥ 2020, `atvType` empty
  (drops hybrids, EVs, PHEVs, FFV, diesel, CNG), gasoline fuel types only. 6,142 rows at
  first fetch (2026-09-30), years 2020–2027. The source updates continuously; re-fetching
  changes the numbers, so topics should record the FETCHED date they used.
