# NOTES — 000-test-linear-regression / L1 (TEST VIDEO)

Running log for the next session (human or agent). Newest first.

## Status
- script: draft, agent-written (test video; not for publication) · shotlist: approved (by the agent, for the test)
- scenes: 5/5 pass the §8 review loop at 720p (sheets in renders/)
- audio: Kokoro placeholders for all 15 beats · final: `-q h` test renders with the PLACEHOLDER watermark
- purpose: exercise the whole pipeline; see channel/pipeline.md §6

## Nitish's notes
(timestamped watch notes go here; the agent reads this section)

## Log

### 2026-10-01 — Built end to end (agent)
What the build exposed, in the order found — each fixed and pinned with a test:
- **Parallel renders raced on Manim's text/TeX cache** (`.media/texts/<hash>_.svg` unlinked by
  one process while another read it). Fix: one media dir per render (`renders/.media/<render>/`).
- **`TransformMatchingTex(key_map=…)` raises in Manim 0.21** when the mapped parts have different
  glyph counts (`FadeTransformPieces` zips families strictly). Dropped `key_map` from
  `equations.morph`; mismatched terms fade out/in, which reads fine.
- **A `GaussianSlice` animated with `AnimationGroup(Create(curve), FadeIn(fill))` was never in the
  scene** — the scene adds the AnimationGroup's own `Group(curve, fill)`. Updaters on the slice
  silently never ran: the two bells in Scene 4 froze at 1500 kg while the band swept. Only visible
  in frames; confirmed with an instrumented render (`--disable_caching`, 0 updater calls). Fix:
  `appear()` passes `group=self`. Lesson: **with the partial-movie cache warm, cached plays do not
  execute animation code at all**, so instrumented probes must disable caching.
- **Caption cards drawn on top of each other** in vertical renders: Manim snapshots the moving
  mobjects at play start, so swapping a holder's children mid-play leaves the old card drawn.
  Fix: build all cards up front, toggle opacity. `DecimalNumber.set_value` already works around
  the same thing (it zeroes the old glyphs' points).
- **Updaters without `dt` do not run during waits** (Manim only renders per-frame when a
  time-based updater exists). Captions and Ledger use `(m, dt)` updaters.
- **End card text over faded tick numbers** — caught by the new text-overlap check; the chart now
  fades out fully.
- The ledger showed `1,136 kg`; `group_with_commas=False`.
Timings (M4): 480p 5 scenes ≈ 15 s with `--jobs 3`; 720p ≈ 25 s; 1080p60 see pipeline log.
Equation panel: the long `noise` equation scales to ~0.7 to fit the 40% panel (≈30 px x-height at
1080p — above the 28 floor, but the smallest text in the video).

### Open
- Marks in *recorded* audio still interpolate by word position until `tools/align.py` exists.
- Only 16:9 and 9:16; Instagram feed 4:5 needs `layout.apply_orientation(aspect)` generalised.
- No music bed / ducking, no intro/outro stingers, no thumbnail tool yet.
- The `noise` equation would read better on two lines in the panel.
- Scene 5's end card could carry the channel mark; none exists yet (AGENTS.md mascot rules).
