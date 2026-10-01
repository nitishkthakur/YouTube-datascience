# Shot list — 030-regression-is-conditional-distribution / L1

Drafted by the agent from script.md (skill: draft-shotlist), edited and approved by Nitish.
Narration is quoted from script.md and never changed here. Durations are estimates until
audio exists; the audio decides. `extend` = silent visual time a beat may run past its speech
(AGENTS.md §7).

Status: draft — pilot Scene 3 only. Changes from the AGENTS.md §5.2 original are marked ⚑.

## Scene 3 — "From marginal to conditional" (~27s)
Layout: plot-left-60 / eq-right-40
Persistent: scatter of **all 398 cars** (mpg vs weight in kg, UCI Auto MPG), DATA ⚑ (was 60
points: with 60, the band at 1500 kg holds only 3–4 cars — too few to fit a Gaussian)
Axes: weight 700–2400 kg (ticks 1000/1500/2000), mpg 5–50 (ticks every 10), MUTED

### Beat 3.1 (est. 0–7s · speech ~5s · extend 2s)
NARRATION: "Ignore weight for a second. [[values]] Here is every mpg value we ever saw."
- from the start: points collapse horizontally onto the y-axis (Transform, 2s)
- at [[values]]: rotated Gaussian grows out of the y-axis, fitted to those 398 values
  (MLE: μ = 23.5, σ = 7.8), CONCEPT
- labels μ (mean line) and σ (dashed segment from μ to μ+σ, ending on the curve), CONCEPT
- equation panel: eq `marginal`

### Beat 3.2 (est. 7–14s · speech ~4s · extend 3s)
NARRATION: "Now suppose I tell you the car [[weighs]] weighs 1500 kg."
- points return to the scatter (Transform, 1s); marginal Gaussian dims to 30% as a reference
- at [[weighs]]: vertical band at x = 1500 kg, **width 150 kg** ⚑ (was ≈100 kg: at 100 kg the
  band holds as few as 4 cars near 2100 kg and σ collapses to 0.3), PARAM, label "1500 kg"
- points inside the band become DATA_FOCUS; the rest fade to 20% opacity
- new Gaussian along the band, bulging left: **narrower, lower centre** ⚑ (was "higher
  centre"; the data give μ ≈ 19.7 vs the marginal 23.5, σ ≈ 3.5 vs 7.8; 45 cars in the band), CONCEPT
  — fitted to the cars in the band, weighted towards the band's centre (Epanechnikov)
- equation morphs `marginal` → `conditional` (TransformMatchingShapes ⚑ — matches glyphs, so
  script.md needs no {{ }} markup)

### Beat 3.3 (est. 14–27s · speech ~3s · extend 9s)
NARRATION: "Slide the weight and the whole distribution moves."
- band label fades; band SLIDES left 1500 → 900 kg (2s, smooth) — no teleport ⚑ — carrying
  the Gaussian; the mean trace grows on this pass too
- band sweeps 900 → 2200 kg over 5s (linear); highlighted points and the Gaussian follow
  (σ(x) visibly shrinks, ≈4.9 at 900 kg → ≈1.1 at 2200 kg — the equation's σ(x)); the ledger
  under the equation reads x, μ(x), σ(x), n live ⚑ (n falling to 9 makes the thin-data spike honest)
- the Gaussian's mean leaves a trace, MODEL — that trace IS the regression curve
  E[Y | X = x] ⚑ (local estimate, so it curves from ~33 to ~12 mpg; not a straight line)
- hold for the rest of the budget, then indicate the trace (stroke-width pulse, MODEL)
- equation terms are coloured by role (X=x PARAM, μ/σ CONCEPT) and morph term-wise ⚑

## Proposed marks (added to script.md, silent — approve or move)
- 3.1 `[[values]]` before "Here is every mpg value…" — the Gaussian appears
- 3.2 `[[weighs]]` before "weighs 1500 kg" — the band appears

## Components built for this scene
- `dsanim.stats` — normal_fit (MLE), band_weights / local_normal (Epanechnikov band fit)
- `dsanim.components.gaussian.GaussianSlice` — sideways Normal density with μ line, σ segment.
  All slices share one peak width (shape, not density height): σ varies ~7× in the sweep.
- `dsanim.components.scatter.Scatter` — collapse / focus_band / unfocus
- `dsanim.components.conditional` — band, conditional_slice, mean_point
