# Decisions log

Short records of project-level decisions and why, newest first. Topic-specific decisions go
in that topic's NOTES.md. When a decision changes AGENTS.md, note it here too.

## 2026-09-30 (later) — Pilot Scene 3
- **Silent visual time**: `self.beat(id, extend=s)` lets a beat's animations run `s` seconds past
  its speech (sweeps, holds). Budgeted per beat in the shot list; default 0. Chosen over
  script pauses (Nitish would have to time them while recording) and over compressing the
  scene to the speech. AGENTS.md §7.
- **Safe-area check at the end of every beat** (`DSScene._check_safe_area`): warning while
  iterating, `SafeAreaViolation` in final renders. Non-drawn mobjects (ValueTracker) ignored.
- **Local band estimate** (`dsanim.stats.local_normal`, Epanechnikov, half-width 75 kg) for
  μ(x), σ(x) in the pilot, all 398 cars on screen. See the tier NOTES.md for the numbers.
- **`typography.symbol()`**: a whitelist of single symbols (μ, σ, β₀ …) for labelling diagrams;
  anything longer is an equation and must come from script.md via `self.eq()`. Lint E3 now
  also flags `T.math()` in topic scenes.
- **Gallery goldens** cover every gallery scene in both orientations
  (`tests/regression/test_gallery_frames.py`), not just the style sheet.

## 2026-09-30 — Project initialisation
- **Package** `dsanim` in `src/dsanim/` (was `lib/`): installable, unambiguous import name;
  `lib/` collided with the Python .gitignore template.
- **Environment**: uv project (`uv run ...`), not `uv tool install manim` — a tool install
  cannot import our package or third-party libs. Python 3.12. ManimCE pinned `>=0.20,<0.22`
  (0.21.0 installed).
- **Math typesetting**: XeLaTeX + unicode-math, STIX Two Math / STIX Two Text, via TinyTeX
  (per-user, ~/Library/TinyTeX). Accepted: slightly heavier TeX than pdflatex.
- **Narration**: our own thin layer (`dsanim.narration`, `DSScene.beat()`) instead of
  manim-voiceover. Reasons: manim-voiceover went ~2 years without a release (0.4.0 in
  June 2026), its RecorderService needs PyAudio + pynput accessibility permissions, and our
  audio is recorded outside Manim (Audacity) per beat anyway. Same idea — timing from audio
  duration and bookmarks — ~150 lines we control.
- **Placeholder voice**: Kokoro-82M (Apache-2.0) via `tools/tts_placeholder.py`. Final
  renders (-qh/-qk) refuse placeholder audio.
- **Audio outside git**: `assets/audio/` is git-ignored; set `DSANIM_AUDIO_DIR` to keep it
  elsewhere (e.g. a synced drive).
- **Topics**: `topics/<NNN-concept>/<L1|L2|L3>/` — one concept folder, one sub-folder per
  tier video. Gapped numbering (010, 020, …).
- **script.md is machine-parsed**: beat headings, `[[marks]]`, ```math id=``` blocks. Scenes
  reference beats/equations by ID so narration and LaTeX cannot drift from the script.
- **Datasets**: UCI Auto MPG (CC BY 4.0) as the classic; EPA fuel economy 2020+ (public
  domain) as the fresh one. Runner-up for later: Stack Overflow survey salary vs experience
  (ODbL) for heteroscedasticity/Gamma.
- **Text sizing**: measured Manim `font_size` N ≈ N px x-height at 1080p, so "px-equivalent"
  in AGENTS.md = `font_size`. Vertical renders scale all text ×1.25 (`VERTICAL_TEXT_SCALE`) so
  the smallest size (32) meets the 40 px Shorts minimum.
- **Testing policy** (Nitish): tests for all code, regression tests per major feature, smoke
  tests. Layers in tests/unit, tests/regression (goldens), tests/smoke; `slow` marker for
  renders/TTS. AGENTS.md §14.
- **Agent guard-rails**: PostToolUse lint hook (blocks ManimGL-isms, stray hex colours, inline
  LaTeX / Manim colour constants in topic scenes); PreToolUse approval prompt on any topic
  `script.md` edit. Skills: new-topic, draft-shotlist, build-scene, render-review, narration.
- **AGENTS.md corrections**: `--disable_caching_warning` is not a Manim flag (removed);
  `dvisvgm` added to TeX requirements; ManimCE version range updated to 0.20–0.21.
- **Published topics are tagged** `published/<concept>/<tier>` so they can be re-rendered
  exactly even after `dsanim` changes.
