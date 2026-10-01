---
name: produce
description: Run the deterministic pipeline for a tier (status → renders at 480p/720p/1080p → assembled videos with chapters and subtitles → vertical chunks), then review the outputs and report what Nitish still owes. Use when asked to "render the video", "make the shorts", "produce", or "what's missing to publish".
---

# Produce a tier (channel/pipeline.md)

1. `uv run python tools/status.py <tier>` — read the NITISH / CODE / AGENT lists. If scenes are
   missing, stop and use `build-scene`; if the script is not frozen or audio is missing, say so.
2. Decide the mode:
   - real production: `uv run python tools/pipeline.py <tier> --qualities l m h --jobs 3 --sheet`
     (fails, by design, on an unfrozen script or placeholder audio at 1080p);
   - test production (Nitish not recording yet): add `--allow-placeholder` — outputs carry a
     PLACEHOLDER watermark and must never be published.
   Long runs go in the background; do not block the session on a 1080p60 render.
3. Review, with evidence (skill `render-review`): every `renders/*_m.sheet.png`; the seam lines
   printed by assemble (`HARD CUT` means scene N's end state ≠ scene N+1's first frame — check
   the shot list's TRANSITION); `publish/chapters.txt` titles and times; a few SRT cards; one
   vertical chunk's sheet (`tools/contact_sheet.py renders/shorts/<name>_h.mp4 --every 3`).
4. Append to NOTES.md: render times, seam report, anything you changed, open questions.
5. Run `uv run python tools/status.py <tier>` again and report its "next" list verbatim — that
   is what Nitish must do before publishing. Include paths of the assembled videos and shorts.
