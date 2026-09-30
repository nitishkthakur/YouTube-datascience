---
name: draft-shotlist
description: Draft or update a tier's shotlist.md from its script.md, beat by beat, following AGENTS.md §5.2. Use after Nitish has written (not necessarily frozen) script.md and before any scene code.
---

# Draft a shot list

Inputs: `topics/<concept>/<tier>/script.md` (read it fully), root AGENTS.md §4–§5, the
concept README (shared notation/datasets), `channel/curriculum.md` (what the viewer already knows).

1. `uv run python tools/check_script.py <tier_dir>` — fix nothing in the script; if it fails
   to parse, show Nitish the error.
2. For each scene and beat, write in `shotlist.md`:
   - scene header: title, estimated length (from check_script durations), layout
     (`plot-left-60 / eq-right-40` default), persistent elements;
   - per beat: `NARRATION:` quoted **verbatim** from script.md; `FOCUS:` the one thing the
     eye must be on; bullet list of what enters/changes/is emphasised, each with its colour
     **role** (DATA, DATA_FOCUS, CONCEPT, PARAM, MODEL, ERROR); `sync:` which `[[mark]]` starts
     which animation; `equations:` ids and which terms appear at which mark; `STATE (end):`
     every persistent object's state; `TRANSITION:` how it becomes the next beat's first frame
     (nothing jumps). Treat `extend` seconds as choreography: every silent second has a
     visible change or a hold with a stated reason.
3. Every animation must explain a state change (no decoration). Respect run-time defaults
   (1.0 s, entrances 0.8 s, sweeps 4–6 s) and ≤12 words of on-screen text.
4. Where a sync point is needed but the script has no mark, **propose** the mark in a
   "Proposed marks" list at the end — do not edit script.md yourself.
5. Where layout or intent is ambiguous, ask Nitish ONE precise question rather than guessing.
6. Identify which dsanim components are needed; list new ones under "Components to build".
7. Set `Status: draft` and append a line to the tier's NOTES.md.
