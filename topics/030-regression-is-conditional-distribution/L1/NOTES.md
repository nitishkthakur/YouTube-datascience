# NOTES — 030-regression-is-conditional-distribution / L1

Running log for the next session (human or agent). Newest first. Record decisions, things
that broke, render times, and anything you were unsure about.

## Status
- script: draft (Scene 3 only, copied from AGENTS.md §5.2; marks [[values]] [[weighs]] added — need Nitish's OK)
- shotlist: draft, Scene 3 only (⚑ marks the changes from the original)
- scenes: `s03_conditional.py` passes the §8 loop at -qm in both orientations (placeholder voice)
- audio: Kokoro placeholders for 3.1–3.3 (4.9 s / 4.0 s / 3.1 s); nothing recorded yet
- final: **blocked** — `-q h` refuses placeholder audio; Nitish records the 3 lines, then re-render

## Log

### 2026-10-01 — Scene 3 reworked after the pedagogy critique (agent)
Applied: no teleport (band slides 1500 → 900 in 2 s, trace grows on that pass too); equation
terms coloured by role (X=x PARAM, μ/σ CONCEPT) and morphed term-wise (`self.eq(..., terms=,
roles=)` + `components.equations.morph`); live ledger x / μ(x) / σ(x) / n under the equation;
`slice.appear()` + `set_params` updater instead of `always_redraw`; static "1500 kg" label
dropped before the slide; `self.wait(b.remaining…)` instead of a fixed HOLD (lint W1).
Not applied (needs Nitish's words or a design call): collapse-as-conditioning at [[weighs]],
dot-histogram collapse in 3.1, marginal drawn in a margin strip, narration additions
(critique items 1, 2, 7, 12). The 000 test video's Scenes 2–4 show items 1 and 4 working.
Sheet: renders/Scene03_m.sheet.png (both orientations pass the safe-area and overlap checks).

### 2026-09-30 — Pilot Scene 3 built (agent)
Decisions (asked, Nitish chose):
- **All 398 cars** on screen, not 60. With 60, the band at 1500 kg held 3–4 cars.
- **Local band estimate** for μ(x), σ(x): Epanechnikov weights, half-width 75 kg (150 kg band).
  h=50 was visibly jumpy and dropped to n=4 near 2100 kg; h=75/100 are smooth; 75 keeps the
  band reading as "a car that weighs 1500 kg". The mean trace is therefore a curve
  (~33 → 12 mpg), not the OLS line. OLS as "the special case" is a later scene.
- **Silent visual time** via `self.beat(id, extend=s)`: speech is ~12 s but the shot list needs
  ~27 s (collapse, sweep, hold). extend = 2 / 3 / 9 s for beats 3.1 / 3.2 / 3.3.
- **-qh with recorded audio**, not a placeholder override.
Facts checked against the data (shot list corrected, ⚑):
- marginal μ=23.5 σ=7.8; conditional at 1500 kg μ=19.7 σ=3.5 (n=45) — *lower* centre than the
  marginal, not "higher" as the original shot list said; σ(x) ≈ 4.9 at 900 kg → 1.1 at 2200 kg.
Things that broke:
- `always_redraw`/`Create` leave the *submobjects* of a `GaussianSlice` as top-level scene
  objects; removing the group is not enough — remove `.curve` and `.fill` too.
- First safe-area check flagged a `ValueTracker` (it has points but is never drawn). The check
  now ignores non-drawn mobjects. `AbstractImageMobject` must be imported from
  `manim.mobject.types.image_mobject`, it is not re-exported by `manim`.
- Thumbnails at 640 px misled me twice (the faded marginal crossing the live slice looked like
  a ghost curve). Extract the full-size frame before "fixing" what a thumbnail shows.
- The band spanned the full y-range and sat on the x-axis line → `band(..., y_span=(2, 48))`.
Render times (M4, 16 GB): -ql 6 s, -qm 7–8 s for the 23 s scene. TeX for the two equations is cached.
Open questions for Nitish:
- Equation size in the right panel (fits the region width; reads small at 720p).
- At 900 kg the conditional slice (bulging left) overlaps the faded marginal (bulging right
  from the y-axis). Kept as a reference overlay; say if it reads as clutter.
- Vertical: the caption band is empty (burned-in captions not built yet, AGENTS.md §10).
- The σ segment is drawn from μ to μ+σ at the curve's inflection width — is that the
  labelling you want, or a horizontal ±σ bracket?
