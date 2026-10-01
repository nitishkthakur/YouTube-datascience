# topics — one concept per folder, one video per tier

Layout: `topics/<NNN>-<slug>/` (concept, README.md) → `L1/`, `L2/`, `L3/` (one video each).
Create with `uv run python tools/new_topic.py <NNN-slug> <L1|L2|L3>`; add the concept to
`channel/curriculum.md`. Never edit `_template/` for one topic's needs.

## Order of work inside a tier (root AGENTS.md §5–§8)
0. `outline.md` — Nitish's points, in his order. Ask for it; never invent the material.
1. `script.proposed.md` — the agent's expansion of the outline in full script format, every
   addition marked (skill `draft-script`). `script.md` is Nitish's: he promotes the proposal
   himself; every agent edit to it needs his approval (hook). Never change narration or math.
2. `shotlist.md` — agent drafts from the script (skill `draft-shotlist`), Nitish approves.
3. `scenes/sNN_<slug>.py` — one `DSScene` subclass per file, one scene at a time (skill
   `build-scene`). Beats are `with self.beat("N.M") as b:` blocks; equations via
   `self.eq("<id>")`; colours via `P.<ROLE>`; positions via `self.layout`.
4. Review loop at `-qm` with an inspected contact sheet (skill `render-review`).
5. Narration: placeholder → recorded (skill `narration`).
6. `NOTES.md` — append what you decided, what broke, render times. Newest first. Nitish's watch
   notes go under "## Nitish's notes"; read them before re-rendering.
7. Produce: skill `produce` (tools/pipeline.py) — renders every quality, assembles, cuts Shorts,
   and prints what Nitish still owes.

## Rules
- Scene code imports only `manim`, `dsanim` and the tier's `common/` (put on PYTHONPATH by
  tools/render.py). `common/stage.py` builds what every scene shares — axes, data, line, equation
  tokens — so scene N's end state is scene N+1's first frame. Anything reusable across topics
  goes to `src/dsanim/`.
- Equations: `self.eq("<id>", terms=[...], roles={...})` — `terms` must concatenate to the
  script's LaTeX (checked at runtime); morph with `components.equations.morph`, reveal terms with
  `hide`/`reveal`. Live numbers: `components.ledger.Ledger`. Gaussian slices appear with
  `slice.appear()` (never `Create(slice.curve)` — the slice would not be in the scene and its
  updaters would never run).
- Lint (runs automatically as a hook): no inline LaTeX (E3), no Manim colour constants (E4),
  no hex colours (E2), no ManimGL (E1); fixed `self.wait(n)` warns (W1).
- Both tiers of a concept share notation and datasets; record them in the concept README.
- `renders/` is git-ignored. Contact sheets referenced in reports live there.
- Shorts are the same scene rendered with `--vertical`; `shorts/` only lists the chosen beats
  and caption config.
