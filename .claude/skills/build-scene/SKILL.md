---
name: build-scene
description: Implement ONE scene of a topic from its approved shot list — dsanim components (with tests and gallery scenes), the DSScene code, then the render-review loop. Use when Nitish asks to build/animate a specific scene.
---

# Build one scene

Preconditions: script.md parses; shotlist.md for this scene is approved. One scene per run.

1. Read root AGENTS.md, `src/dsanim/AGENTS.md`, `topics/AGENTS.md`, the scene's shot list,
   and the tier's NOTES.md.
2. **Components first.** Anything reusable (Gaussian slice, band, sweep…) goes in
   `src/dsanim/components/<name>.py`, sized from a `layout.Region`, coloured by role.
   For each: unit tests (`tests/unit/`), a `gallery/<name>.py` scene, and for major ones a
   golden-frame regression test (`tests/regression/`). Render the gallery scene at `-qm
   --sheet` and inspect it.
3. **Scene file** `topics/<concept>/<tier>/scenes/sNN_<slug>.py`:
   ```python
   from manim import *
   from dsanim import data, palette as P
   from dsanim.scene import DSScene

   class Scene03(DSScene):
       def construct(self):
           L = self.layout
           # --- Beat 3.1 — <what changes> ---------------------------------
           with self.beat("3.1") as b:
               ...  self.play(..., run_time=b.until("collapse"))
   ```
   - equations only via `self.eq("<id>")`; data only via `dsanim.data`; positions via
     `self.layout` regions; no fixed waits — use `b.until/wait_until/remaining`.
   - Make it work for `self.vertical` too if the beat is listed in `shorts/`.
4. If no audio exists yet, generate placeholders (skill `narration`) so timing is real.
5. `uv run python tools/check_script.py <tier_dir> --scenes`
6. Run the **render-review** skill for this scene. Iterate until it passes.
7. `uv run pytest` (full). Append to NOTES.md: decisions, render time, open questions.
8. Report per root AGENTS.md §12: what was rendered, contact sheet path, what you checked,
   what you're unsure about, test results.
