---
name: new-topic
description: Scaffold a new concept folder and/or tier video (L1/L2/L3) under topics/ from the template, and register it in channel/curriculum.md. Use when Nitish wants to start a new video or a new tier of an existing concept.
---

# New topic / tier

1. Confirm the concept slug and number with Nitish if not given. Numbers come from
   `channel/curriculum.md` (steps of 10; insert with an in-between number, never renumber).
2. Run: `uv run python tools/new_topic.py <NNN-slug> <L1|L2|L3>`
3. Update `channel/curriculum.md` (row, dependencies, tiers, status) and the concept
   `README.md` (tiers table, dependencies, shared dataset/notation).
4. Do NOT write narration into the new `script.md` — it is Nitish's. Tell him the file is
   ready and point to the format comment inside it (root AGENTS.md §5.1).
5. Run `uv run pytest -m "not slow"` and report.
