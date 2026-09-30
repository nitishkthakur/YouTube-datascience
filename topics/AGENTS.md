# topics — one concept per folder, one video per tier

Layout: `topics/<NNN>-<slug>/` (concept, README.md) → `L1/`, `L2/`, `L3/` (one video each).
Create with `uv run python tools/new_topic.py <NNN-slug> <L1|L2|L3>`; add the concept to
`channel/curriculum.md`. Never edit `_template/` for one topic's needs.

## Order of work inside a tier (root AGENTS.md §5–§8)
1. `script.md` — Nitish's. Agents may only draft it when explicitly asked (e.g. from his
   voice memo), and every edit needs his approval (hook). Never change narration or math.
2. `shotlist.md` — agent drafts from the script (skill `draft-shotlist`), Nitish approves.
3. `scenes/sNN_<slug>.py` — one `DSScene` subclass per file, one scene at a time (skill
   `build-scene`). Beats are `with self.beat("N.M") as b:` blocks; equations via
   `self.eq("<id>")`; colours via `P.<ROLE>`; positions via `self.layout`.
4. Review loop at `-qm` with an inspected contact sheet (skill `render-review`).
5. Narration: placeholder → recorded (skill `narration`).
6. `NOTES.md` — append what you decided, what broke, render times. Newest first.

## Rules
- Scene code imports only `manim` and `dsanim`. Anything reusable goes to `src/dsanim/`.
- Lint (runs automatically as a hook): no inline LaTeX (E3), no Manim colour constants (E4),
  no hex colours (E2), no ManimGL (E1); fixed `self.wait(n)` warns (W1).
- Both tiers of a concept share notation and datasets; record them in the concept README.
- `renders/` is git-ignored. Contact sheets referenced in reports live there.
- Shorts are the same scene rendered with `--vertical`; `shorts/` only lists the chosen beats
  and caption config.
