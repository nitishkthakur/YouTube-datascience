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

### 2026-10-01 (later) — Round-2 review fixes (agent)
Reviewed at 720p after these changes (renders/): Scene01_m.sheet.png, Scene02_m.sheet.png,
Scene03_m.sheet.png, Scene04_m.sheet.png (band parks at 1300 kg; both bells legible; OLS σ
violet), Scene05_m.sheet.png; shorts/what-the-line-leaves-out_h.sheet.png (captions, ledger,
watermark in the gutter). Seams: all continuous (≤0.3% pixels change).
Code review found a blocker before any real recording: with Manim's partial-movie cache warm, a
cached play skips `add_sound`, so a re-render of an unchanged scene shipped **without
narration** (and advanced time by the unquantised duration). Fix: caching is now off for every
render (`config.disable_caching` + `--disable_caching`); incremental work is per scene
(`render_all` keeps scenes whose inputs hash is unchanged) and `tests/regression/
test_render_twice.py` renders twice into one media dir and checks audio + identical timings.
Also from the reviews: finals refuse missing narration and stale recordings (`audio_manifest`),
assemble/make_shorts refuse renders whose inputs changed (`.inputs.sha`), PCM intermediates with
one AAC encode (no priming gaps at seams), two-pass loudness to −14 LUFS + BT.709 tags + crf 18
at h/k (the h master measured −25.5 LUFS before), `-t` cuts, `late` flag on marks, stroke-aware
safe-area boxes, render logs per scene, shot-list approval bound to a content hash
(`tools/approve.py`), `title:` in the description, `.env` for the audio root, phrase-boundary
two-line captions, watermark in the gutter. Design: OLS σ is violet everywhere (the line's one
constant width), the band parks at 1300 kg under "so does its spread" so both bells stay
legible, equations fill the panel (≤1.3×), dots 6 px. The stage builder moved into
`dsanim.components.chart`; `common/stage.py` keeps only this tier's constants.

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
- Marks in *recorded* audio still interpolate by word position until `tools/align.py` exists —
  **build it before the first real recording** (both reviews: this bites first).
- Hook card for Shorts (1.5 s from `hook:`), end card held 8–10 s with an end-screen region,
  a CC0 music bed with ducking, `tools/thumbnail.py`, a channel mark.
- Only 16:9 and 9:16; Instagram feed 4:5 needs `layout.apply_orientation(aspect)` generalised.
- No music bed / ducking, no intro/outro stingers, no thumbnail tool yet.
- The `noise` equation would read better on two lines in the panel.
- Scene 5's end card could carry the channel mark; none exists yet (AGENTS.md mascot rules).
