---
name: render-review
description: The mandatory review loop (AGENTS.md §8) — render a scene at -qm, build the contact sheet, open and inspect it against a checklist, fix and repeat. Use before reporting any scene or gallery component as done.
---

# Render → contact sheet → inspect

1. Lint is automatic (hook). Iterate at `-ql` first:
   `uv run python tools/render.py <scene_file> <Scene> -q l`
2. Review render: `uv run python tools/render.py <scene_file> <Scene> -q m --sheet`
   (add `--vertical` for beats chosen as Shorts, and review that sheet too).
   If a beat raises `NarrationOverrun`, shorten the animation — never speed the audio.
3. **Open the `.sheet.png` with the Read tool and inspect it.** Check every tile:
   - nothing crosses the red safe-area outline;
   - no text overlaps text or data; no clipped equation; text large enough;
   - colours match roles (DATA grey, CONCEPT teal, PARAM amber, MODEL violet, ERROR coral);
   - each beat's end state (last tile before the next beat, and the `(end)` tile) matches
     the shot list; ≤12 words of non-equation text on screen.
   Use `--every 1` or extract a specific frame with ffmpeg if a transition needs a closer look.
4. Fix → re-render → re-inspect until clean.
5. Report: the sheet path, what you checked, anything you're unsure about. Never "looks
   great" without the sheet. Never run `-q h`/`-q k` until `-q m` passes; final renders run
   in the background (`run_in_background`) and refuse placeholder audio.
