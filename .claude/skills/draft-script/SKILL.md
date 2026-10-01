---
name: draft-script
description: Turn Nitish's outline.md (his points, in his order) into script.proposed.md in the real script format, with clearly marked additions he can accept or cut. Use when a tier has an outline but no script yet, or when Nitish asks for a proposed/expanded version of his material.
---

# Draft the proposed script (step 2 of the standard procedure, AGENTS.md §7)

Inputs: `topics/<concept>/<tier>/outline.md` (Nitish's points, in sequence — this is the
substance and the order; do not reorder or drop anything), the concept README (dataset,
notation, Decisions), `channel/curriculum.md` (what the viewer already knows), AGENTS.md §1
(the thesis and the fixed shape: intuition → formal → how it breaks → practitioner checks).

1. If `outline.md` is missing, ask for it — do not invent the material.
2. Write `script.proposed.md` in the exact `script.md` format (front matter; `## Scene N —
   "Title"`; `### Beat N.M`; narration paragraphs; `[[marks]]`; ```math id=…``` blocks).
   Keep Nitish's wording where he gave it; where he gave a point, write the narration for it.
3. Mark every addition so he sees at a glance what he may have missed: a blockquote directly
   above the beat, `> PROPOSED ADDITION — <why in one line>`, and list them all in a
   "## What I added and why" section at the top (hook, a missing step, a "how it breaks"
   beat, a practitioner check, a transition, foreshadowing of a later concept). Additions are
   suggestions; keep them easy to delete as whole beats.
4. Equations: exactly what the maths requires; never simplify or "correct" his (AGENTS.md
   §9). Flag anything you believe is wrong in the outline with `> QUESTION:` rather than
   changing it.
5. Run `uv run python tools/check_script.py <tier>/script.proposed.md` so the format parses.
6. Tell Nitish: the file path, the number of beats, the estimated speech length, and the
   list of additions. He edits and promotes it to `script.md` himself (or asks you to copy
   it over — that edit goes through the approval hook).
