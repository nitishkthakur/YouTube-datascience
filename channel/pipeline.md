# The production pipeline: inputs, outputs, and the two ways to run it

This is the contract between Nitish, the deterministic tools, and an agent. If something is
not listed as Nitish's input here, he does not have to provide it.

## 1. What Nitish provides (and nothing else)

| # | Input | Where | When | Checked by |
|---|---|---|---|---|
| 1 | **Outline** — his points, in sequence (+ must-say phrasing, data, length) | `topics/<concept>/<tier>/outline.md` | first | the agent asks for it if missing |
| 1b | **Script** — he edits the agent's `script.proposed.md` (additions marked) into `script.md`: narration in beats, `[[marks]]`, equations with ids | `topics/<concept>/<tier>/script.md` | after the proposal | `tools/check_script.py`, parse errors are explicit |
| 2 | **Decisions the shot list needs** — dataset, estimator, band width, what each Short is | concept `README.md` / answers to the agent's questions | before scenes | agent asks ONE question at a time (AGENTS.md §12) |
| 3 | **Shot-list approval** | `uv run python tools/approve.py <tier>` (binds `Status: approved <hash>` to the text; later edits show as "edited after approval") | before scene code | `status.py` |
| 4 | **Freeze** | `script.md` → `status: frozen` | when words are final | final renders refuse unfrozen scripts |
| 5 | **Narration** — one WAV per beat, exported from Audacity by labels, then `tools/audio_manifest.py register` | `$DSANIM_AUDIO_DIR/<concept>/<tier>/s03_b02.wav` (spec: `assets/audio/README.md`) | after freeze | `status.py` counts recorded / placeholder / missing and reports **stale** recordings (words changed since) |
| 6 | **Watch notes** on the 720p review renders | tier `NOTES.md`, under "Nitish's notes": `- [m] 0:47 S3 b3.2 — note` | after review renders | agent reads them, re-renders, marks each `✓ <sha>` |
| 7 | **Shorts choice** (optional — the agent can propose) | `shorts/chunks.yaml` | any time | `make_shorts.py` |
| 8 | **Publish metadata** — `title:` + description, thumbnail (1280×720 min, 16:9, < 2 MB) | `publish/description.md`, `publish/thumbnail.png` | last | `status.py` |

**You never hand-edit:** `scenes/`, `common/`, `renders/`, generated `publish/` files,
`audio_manifest.json`. Edits to a frozen script: set `status: draft`, edit, re-freeze; recorded
beats whose words changed are reported stale and must be re-recorded.

Run `uv run python tools/status.py <tier>` at any point: it prints every item above with ✓/✗ and
who owes it (NITISH / CODE / AGENT), then a "next" list.

## 2. What the code produces (deterministic, no judgement)

`uv run python tools/pipeline.py <tier> --qualities l m h [--allow-placeholder] [--jobs 3] [--sheet]`

| Step | Tool | Output |
|---|---|---|
| placeholder voice (only with `--allow-placeholder`) | `tts_placeholder.py` | `…/placeholder/sNN_bMM.wav` + word timings |
| render every scene, 16:9, at each quality | `render_all.py` | `renders/<Scene>_<q>.mp4` + `.beats.json` (beat/mark/caption times, audio hashes) |
| contact sheets (with `--sheet`, at 720p) | `contact_sheet.py` | `renders/<Scene>_m.sheet.png` |
| one video per quality, loudness −14 LUFS (two-pass), BT.709 tagged, crf 18 at h/k | `assemble.py` | `renders/<topic>_<tier>_<q>.mp4` |
| YouTube chapters, subtitles, reproducibility record, seam report | `assemble.py` | `publish/chapters.txt`, `publish/subtitles.srt`, `publish/manifest_<q>.json` |
| vertical chunks with burned-in captions | `make_shorts.py` | `renders/shorts/<name>_<q>.mp4` |

Qualities: `l` 854×480 @15 (iterate), `m` 1280×720 @30 (review), `h` 1920×1080 @60 (publish),
`k` 3840×2160 @60 (master). Vertical = 1080×1920 at `h`.

Guards that cannot be talked around: a `-q h`/`-q k` render fails if the script is not frozen or
any beat uses placeholder audio — unless `--allow-placeholder`, which produces a **test render**
with "PLACEHOLDER VOICE — NOT FOR PUBLICATION" burned in. Every beat ends on ≥0.5 s of silence;
animations that outrun their narration fail the render; anything outside the 5% safe area
fails a final render; text over text is reported.

## 3. Mode A — deterministic rebuild

Mode A is the **rebuild**: once a tier's scenes exist (authored in Mode B), Nitish can re-record,
change a chunk list or a title, and run `status.py` → `pipeline.py` with no agent involved.
`publish/manifest_<q>.json` records tool versions, the git commit, every scene's duration and
every beat's audio hash; the beat timings and the 480p last frames are pinned by tests, so a
rebuild on the same inputs gives the same timings and frames (encoders are not bit-stable, so
not byte-identical files). Unchanged scenes are not re-rendered.

What Mode A cannot do: turn a script into a shot list or scene code, judge whether a frame
reads well, notice that two bells overlap, choose a thumbnail, or decide that a 9-second silent
sweep is too long. It renders what exists.

## 4. Mode B — agent-assisted

The same tools, driven by an agent that can also *see*: Claude Code today (skills in
`.claude/skills/`), an independent agent on the Claude API later (see §5). The agent:

1. drafts `shotlist.md` from the script, with FOCUS / STATE / TRANSITION per beat, and asks the
   decisions in §1.2 one at a time;
2. builds reusable components in `src/dsanim` (with tests and gallery scenes) and the scene
   code, one scene at a time;
3. runs the review loop — render at 720p, build the contact sheet, **look at it**, fix, repeat —
   and additionally pulls full-size frames when a thumbnail is ambiguous;
4. uses the deterministic checks (safe area, text overlap, overrun, seams) as evidence, then
   applies judgement the checks cannot: pacing of silent `extend` time, whether a label fights
   the data, whether a morph reads, whether the end state matches the shot list;
5. keeps `NOTES.md`, `channel/decisions.md` and the AGENTS.md files current;
6. proposes Shorts chunks and three thumbnail frames.

**Is it worth it?** Yes, for steps 1, 3 and 4 — with a caveat. In the test build the
deterministic layer could not have found three mechanical defects (bells silently not following
the band, caption cards drawn on top of each other, end-card text over faded ticks; details in
the tier's NOTES.md). Each was found by looking at a frame, diagnosed from Manim's source, fixed
in the library and pinned by a test, so Mode A stays correct afterwards. The caveat: the same
loop finds **breakage, not quality** — a sparse frame, a static 10 seconds under the key
sentence, or a colour used for two meanings pass every check. So the review checklist asks, per
beat, "does something change on screen for each clause of the narration?", and every beat's
end frame is read at full size (a contact sheet is downscaled for the model's vision; a tile is
too small to judge). The agent hands back evidence per scene: sheet path, frames read, checklist
lines, and the sha of the scene file reviewed. The render itself gains nothing from an agent.

**Risks, and the guard-rails already in place.** An agent may "correct" maths or words
(script.md edits ask for approval; equations only enter scenes by id; a terms split must
concatenate back to the script's LaTeX); may pad timing to hide slow animation (`extend` is
declared per beat in the shot list, budgets are enforced); may regenerate goldens to go green
(goldens are regenerated only with an explicit flag and must be inspected); may judge from
thumbnails (NOTES record the rule: extract the full frame first).

## 5. An independent agent (not Claude Code)

If Claude Code is not available, the same loop can run as a small program on the Claude API
(Agent SDK). It needs no new pipeline: the tools already return files and exit codes. What it
needs beyond the tools:

- **Tools exposed to the model**: `run(tool, args)` for every `tools/*.py`; `read_image(path)`
  for contact sheets and frames (vision); `read_file` / `write_file` scoped to the tier,
  `src/dsanim` and `tests`; `run_tests`.
- **The same rules**: AGENTS.md as the system prompt; the lint and the script.md guard run as
  pre-write checks in the harness, not as instructions.
- **An approval channel**: the agent works on a branch and opens a PR per scene; Nitish
  approves shot lists, script edits and goldens there. Nothing publishes from the agent.
- **A state file** it can read on every run: `status.py --json`.
- **Budgets**: max renders per scene per run, max image reads, a dollar cap, max wall time,
  and a stop rule ("sheet inspected and no violations" or "ask Nitish") so it cannot loop.
- **Jobs, not calls**: a 1080p60 render of a 10-minute topic takes long enough that it must run
  as a detached job the agent polls (`render_all` already writes a manifest it can wait for),
  never inside one tool call.
- **Branch protection**: the agent cannot push `main`; its run contract is "read
  `status.py --json`, do ONE AGENT item, open a PR with the evidence above".

Cost/benefit: a scene build is tens of tool calls and a handful of image reads; a review pass
is a few. The expensive part is rendering, which is the same in both modes. The agent is
cheap relative to render time; its value is proportional to how often Mode A would have
shipped a frame nobody looked at.

## 6. What the test build proved and what it exposed

Built end to end with a placeholder voice: 5 scenes, 15 beats, 5 equations, 480p/720p/1080p,
chapters, SRT, two vertical chunks with burned-in captions, loudness-normalised and BT.709-tagged
outputs. Two independent review rounds (structure, pedagogy, product, two adversarial code
reviews) were run on it; everything found is either fixed and pinned by a test, or listed under
"Open" in `topics/000-test-linear-regression/L1/NOTES.md`. The one item to do **before the first
real recording** is `tools/align.py` (forced alignment of recorded audio to the script's words),
without which `[[marks]]` in recorded beats are only interpolated.
