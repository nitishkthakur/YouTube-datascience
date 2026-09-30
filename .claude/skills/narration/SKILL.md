---
name: narration
description: Manage beat audio — generate Kokoro placeholder narration, calibrate it to Nitish's pace, check recorded Audacity exports, and re-time scenes to real audio. Use for anything about voice, timing, [[marks]] or audio files.
---

# Narration (AGENTS.md §7)

Audio root: `$DSANIM_AUDIO_DIR` or `assets/audio/` (git-ignored). Beat 3.2 → `s03_b02.wav`.

## Placeholder (before recording)
1. `uv run --extra tts python tools/tts_placeholder.py <tier_dir> [--beats 3.1 3.2]`
2. `uv run python tools/check_script.py <tier_dir>` — confirm every beat shows `placeholder`
   and word timings ok. Placeholders are for timing only and are never shipped.
3. Calibration: if Nitish supplies a sample recording, compare its words/second with the
   placeholder's and set `tts_speed` (and `wpm`) in the script front matter accordingly.

## Recorded (after script is frozen)
1. Nitish exports one WAV per beat from Audacity (labels named `s03_b01`…; see
   `assets/audio/README.md`) into `<audio root>/<concept>/<tier>/`.
2. `check_script.py` must show `recorded` for every beat; report missing/extra files.
3. Re-render each scene (`render-review`). Beats that no longer fit raise
   `NarrationOverrun` → shorten animations. Marks interpolate by word position until
   `tools/align.py` (forced alignment) exists — if a sync point lands visibly wrong, say so
   and propose building align.py (with tests).
4. Never edit, trim, or speed up Nitish's audio without asking.
