# AGENTS.md — Animated Data Science Channel

This file is the constitution for every coding agent (Claude Code, Codex, or other) working in this repository. Read it fully before touching anything. Where it conflicts with your defaults, this file wins.

Folders with their own rules carry a nested `AGENTS.md` (with a `CLAUDE.md` symlink beside it): `src/dsanim/`, `topics/`, `tools/`, `gallery/`, `tests/`. Read the nested file before working in that folder. Project-level decisions and their reasons are logged in `channel/decisions.md`.

---

## 1. What this project is

An educational YouTube channel (plus Shorts, Instagram, Medium articles, and eventually a course site) that teaches data science, machine learning, and econometrics **from the real foundations**, animated 3Blue1Brown-style, with no on-camera presenter.

The pedagogical thesis, which every video must honour:

- Regression is the prediction of a **conditional distribution**, not "predicting y". OLS is the special case where that distribution is Normal and we only model the mean.
- Concepts are introduced in the order their dependencies demand: distributions → conditional distributions → likelihood → entropy and cross-entropy → maximum-entropy families → GLMs → trees and ensembles → anomaly detection → explainability.
- Every topic is taught in a fixed shape: **intuition → formal statement → how it breaks in practice → the checks a practitioner actually runs**. Theory without the practical checks is not a finished video.
- Explanations are **tiered**. Each topic has an entry point for someone meeting it for the first time and a deeper layer for a working practitioner. Tiers are explicit (labelled chapters or separate videos), never blurred.

The audience is people who already write Python but were taught the shallow version of these ideas. Assume competence; never condescend; never skip a step because it "should be obvious".

---

## 2. Stack (do not substitute)

| Layer | Choice | Notes |
|---|---|---|
| Animation engine | **Manim Community Edition (ManimCE) `>=0.20,<0.22`** (0.21.0 installed) | A dependency of the uv project in `pyproject.toml` — run everything with `uv run ...`. **Not** `uv tool install manim`: a tool install cannot import `dsanim`. **Never** use ManimGL / `manimlib` (3b1b's fork). The APIs differ; do not mix them. If unsure which API a snippet is from, check the import: we use `from manim import *`. |
| Language | Python 3.12 (`.python-version`) | Managed with `uv`. `uv sync` installs; `uv sync --extra tts` adds the placeholder-voice model. |
| Equations | LaTeX via `MathTex`, compiled with **XeLaTeX + `unicode-math`** so math is set in STIX Two Math | TinyTeX, per-user at `~/Library/TinyTeX` (not full TeX Live). Needs `dvisvgm`, `standalone`, `preview`, `amsmath`, `unicode-math`, `fontspec`, `xetex`, `cm-super`, `doublestroke`, `dsfont`, `physics`. The template lives in `src/dsanim/typography.py`. |
| Narration sync | Our own layer: `DSScene.beat("3.2")` in `src/dsanim/scene.py` + `src/dsanim/narration.py` | Timing comes from the beat's audio duration and `[[mark]]` word timings. Recorded voice (Audacity) or a **Kokoro-82M** (Apache-2.0) placeholder. manim-voiceover is deliberately not used (see `channel/decisions.md`). See §7. |
| Video assembly | FFmpeg (CLI), Kdenlive for manual edits | Agents use FFmpeg only. |
| Vector assets | SVG, drawn in Inkscape, stored in `assets/svg/` | Mascot, hand cursor, icons. |
| Fonts | Open-licence only: **Inter** (UI/text), **JetBrains Mono** (code), **STIX Two Math** + **STIX Two Text** (math) | Installed via Homebrew casks (`assets/fonts/README.md`). Never a proprietary or unlicensed font. |
| Audio | Own recorded voice; music only from CC0 / YouTube Audio Library | No unlicensed audio, ever. |

**Open-source only.** Do not introduce a dependency that is not OSI-licensed (Remotion, for example, is source-available, not open-source — do not add it).

---

## 3. Repository layout

```
.
├── AGENTS.md / CLAUDE.md      # this file (CLAUDE.md is a symlink); nested ones in key folders
├── pyproject.toml / uv.lock   # the uv project; package `dsanim` is installed editable
├── manim.cfg                  # render defaults only (no colours — see §6)
├── .claude/                   # Claude Code: settings.json (hooks) + skills/ (see §15)
├── channel/                   # above any single video
│   ├── curriculum.md          # concept order, dependencies, tiers, status
│   └── decisions.md           # project-level decision log (why things are the way they are)
├── src/dsanim/                # reusable components — THE visual language (was `lib/`)
│   ├── palette.py             # colours, semantic roles, fonts, sizes, motion defaults (single source of truth)
│   ├── layout.py              # orientation, safe area, plot/equation/caption regions
│   ├── typography.py          # text()/label()/math() factories + XeLaTeX STIX template
│   ├── script.py              # script.md parser (scenes, beats, [[marks]], equations by id)
│   ├── narration.py           # finds a beat's audio, duration, mark times
│   ├── scene.py               # DSScene base class: self.beat(), self.eq(), self.layout
│   ├── data.py                # every dataset (real loaders + seeded synthetic generators)
│   └── components/            # (grows with the pilot) gaussian, scatter, conditional, equations, mascot …
├── gallery/                   # one review scene per component + the style sheet
├── data/                      # curated real datasets (committed) + PROVENANCE.md; cache/ is ignored
├── assets/
│   ├── svg/                   # mascot, hand, icons (all self-made)
│   ├── audio/                 # narration — NOT in git (see §7, assets/audio/README.md)
│   ├── music/                 # CC0 / YouTube Audio Library only, with licence notes
│   └── fonts/                 # README only; fonts are installed system-wide
├── topics/
│   ├── _template/             # copied by tools/new_topic.py
│   └── <NNN>-<slug>/          # one CONCEPT, numbered by curriculum order in steps of 10
│       ├── README.md          # the concept: tiers, dependencies, shared notation/datasets
│       └── L1/ L2/ L3/        # one folder per tier = one video
│           ├── script.md      # MASTER document. Everything derives from this. See §5.
│           ├── shotlist.md    # per-scene, per-beat animation spec. See §5.
│           ├── NOTES.md       # running log for the next session
│           ├── scenes/        # one Python file per scene: s01_marginal.py, s02_conditional.py ...
│           ├── shorts/        # which beats become Shorts + caption config (same scene code, vertical)
│           ├── publish/       # description.md, chapters, thumbnail choice
│           ├── article.md     # website/Medium article, derived from script.md (later)
│           └── renders/       # gitignored
├── tests/                     # unit/ regression/ smoke/ — see §14
└── tools/
    ├── render.py              # render a scene → <tier>/renders/, optional contact sheet
    ├── contact_sheet.py       # frames every N seconds → one PNG grid for review
    ├── check_script.py        # validate script.md; beat/audio/mark/equation report
    ├── lint_scenes.py         # mechanical rule checks (also the Claude Code hook)
    ├── tts_placeholder.py     # Kokoro placeholder narration + word timings
    ├── new_topic.py           # scaffold a concept / tier from topics/_template
    └── fetch_data.py          # (re)download real datasets into data/
```

Rules:
- `src/dsanim/` is shared. Change it deliberately; a change there re-renders every past topic. Published videos are git-tagged `published/<concept>/<tier>` so they can be re-rendered exactly.
- Nothing hard-codes a colour, font, or size. Everything comes from `dsanim.palette` (imported as `P`) and `dsanim.layout`. `tools/lint_scenes.py` enforces this.
- One scene per file. One file renders in under 2 minutes at `-ql`. Split it if not.
- Topic folders are numbered in steps of 10 (`010`, `020`, …) so a concept can be inserted without renaming. The order lives in `channel/curriculum.md`.

---

## 4. Visual language

These are defaults. Nitish owns the palette and may change it — but only in `src/dsanim/palette.py`, never inline. Scenes use the **semantic role names** (`P.DATA`, `P.DATA_FOCUS`, `P.CONCEPT`, `P.PARAM`, `P.MODEL`, `P.ERROR`, `P.TEXT`), not the raw names below.

```python
# src/dsanim/palette.py (current values)
BG        = "#0F1115"   # near-black, slightly warm
INK       = "#E8E6E1"   # primary text
MUTED     = "#6B7280"   # de-emphasised data
ACCENT_1  = "#2DD4BF"   # teal   — "the thing we are talking about"
ACCENT_2  = "#F59E0B"   # amber  — "the second thing / the parameter"
ACCENT_3  = "#A78BFA"   # violet — "the model / the estimate"
DANGER    = "#F87171"   # coral  — errors, residuals, what breaks
```

- **Meaning is carried by colour consistently across the whole channel.** Data is `MUTED`/`INK`; the concept under discussion is `ACCENT_1`; the model's estimate is `ACCENT_3`; anything wrong or residual is `DANGER`. Do not invent new semantics per video.
- **Safe area:** nothing renders within 5% of any edge. Titles and equations sit inside the 90% box. `dsanim.layout` exposes the regions (`self.layout.safe/plot/equation/caption` inside a `DSScene`); use them. Contact sheets draw the safe box in red.
- **Layout grid:** default long-form layout is plot left ~60% / equation panel right ~40%. Shorts use a vertical stack: plot top ~60% / equation bottom ~30% / caption band.
- **Text:** minimum 28px-equivalent at 1080p (measured: Manim `font_size` N ≈ N px x-height at 1080p, so the minimum is `font_size` 28; vertical renders scale all text by 1.25 automatically); never more than ~12 words on screen at once outside of equations; equations appear one term at a time when the narration introduces them.
- **Motion:** every animation must **explain a state change**. No motion for decoration. Default `run_time` is 1.0s; entrances 0.8s; a "sweep" is 4–6s. Use `smooth` rate function unless there is a reason.
- **Do not imitate 3Blue1Brown's palette, pi-creature mascot, or signature phrasings.** Using Manim is fine; looking like a clone is not.
- **Mascot gag:** the cartoon may appear at most once per video, for ≤4 seconds, and is removed by the hand SVG dragging it off-screen. It never speaks over an equation.

---

## 5. The three artifacts (and the order they are written in)

Videos are software. There is a spec, a library, and code. Never write scene code without a shot list. Never write a shot list without a script.

### 5.1 `script.md` — the master document (written by Nitish, reviewed line by line)

Full narration, verbatim, split into **scenes** and **beats**. Every equation that will appear on screen is written here in LaTeX **and checked by Nitish** before any code exists. This is the reviewed artifact; the video, article, and shorts are derived from it.

Header block:

```markdown
---
topic: 030-regression-is-conditional-distribution   # = the concept folder name
tier: L1        # L1 first-contact | L2 practitioner | L3 deep  (= the tier folder name)
status: draft   # draft -> frozen. Only Nitish freezes. Final renders need a frozen script.
title_candidates:
  - "Regression is actually a conditional distribution"
  - "You were taught regression wrong"
hook: the misconception this video fixes, in one sentence
runtime_target: 9m
wpm: 150        # Nitish's speaking pace — timing estimate before any audio exists
tts_voice: af_heart   # placeholder voice; tts_speed calibrates it to Nitish's pace
tts_speed: 1.0
---
```

The body is **machine-parsed** by `dsanim.script`, so its shape is exact:

````markdown
## Scene 3 — "From marginal to conditional"

### Beat 3.2
Now suppose I tell you the car [[band]] weighs 1500 kg.

```math id=conditional
Y \mid X=x \sim \mathcal{N}({{\mu(x)}}, {{\sigma(x)^2}})
```

> Production notes go in blockquotes (or <!-- comments -->). Never spoken.
````

- Plain paragraphs under a `### Beat N.M` heading are the narration, spoken verbatim.
- `[[name]]` is a silent **sync mark**: it names the moment the next word is spoken ("the band appears as I say *weighs*"). Scenes wait for or time animations to marks.
- ```` ```math id=<name> ```` blocks are the **only** source of on-screen equations; ids are unique per script. Manim's `{{ }}` splitting may be used for `TransformMatchingTex`. Scenes get them with `self.eq("<id>")` — never by retyping LaTeX (lint rule E3).
- `uv run python tools/check_script.py <tier_dir>` validates the file and prints each beat's words, estimated/actual duration, audio status, marks and equations.

### 5.2 `shotlist.md` — the animation spec (drafted by the agent from the script, edited by Nitish)

Per scene, per beat: duration, what is on screen, what enters, what changes, what is emphasised. Format:

```markdown
## Scene 3 — "From marginal to conditional" (~35s)
Layout: plot-left-60 / eq-right-40
Persistent: scatter of 60 points (mpg vs weight), MUTED

### Beat 3.1 (0–8s)
NARRATION: "Ignore weight for a second. Here is every mpg value we ever saw."
- points collapse horizontally onto the y-axis (Transform, 2s)
- rotated Gaussian appears along y-axis, fitted to those values, ACCENT_1
- labels μ, σ ; equation panel: eq `marginal` (Y \sim \mathcal{N}(\mu, \sigma^2))

### Beat 3.2 (8–20s)
NARRATION: "Now suppose I tell you the car weighs 1500 kg."
- points spring back to scatter
- vertical band at x=1500, width ≈ 100 kg, ACCENT_2
- points inside band keep INK; the rest fade to 20% opacity
- new Gaussian along the band: narrower, higher centre, ACCENT_1
- sync: band appears at [[band]]
- equation morphs (TransformMatchingTex) → eq `conditional` (Y \mid X=x \sim \mathcal{N}(\mu(x), \sigma(x)^2))

### Beat 3.3 (20–35s)
NARRATION: "Slide the weight and the whole distribution moves."
- band sweeps 900 → 2200 kg over 6s via ValueTracker; Gaussian follows
- the Gaussian's mean leaves a trace, ACCENT_3 — that trace IS the regression line
- hold 3s, then Indicate the line
```

The agent may propose beats and propose `[[marks]]`; it may not change narration. Adding a mark to `script.md` changes no words but still needs Nitish's approval (the `script.md` edit hook asks).

### 5.3 `scenes/*.py` — the code (written by the agent, reviewed by Nitish via rendered frames)

One `DSScene` subclass per scene file, importing only from `manim` and `dsanim`. Every beat is a clearly commented `with self.beat("N.M") as b:` block. Timings come from the audio (§7) — `b.until("mark")`, `b.wait_until("mark")`, `b.remaining` — not from guessed `wait()` values (lint warning W1).

---

## 6. Rendering

`manim.cfg` sets `frame_rate = 60`, 1920×1080 and `media_dir`; quality flags override it. The background colour, fonts and XeLaTeX template are applied in code by `dsanim.scene` (an INI file cannot import `palette.py`).

Always render through `tools/render.py` — it sets PATH for TinyTeX, orientation, the final-render guard, and copies the result to `<tier>/renders/<Scene>_<q>[_v].mp4`:

| Purpose | Command |
|---|---|
| Iteration | `uv run python tools/render.py topics/030-…/L1/scenes/s03_conditional.py Scene03 -q l` (480p15) |
| Review | `… -q m --sheet` (720p30 + contact sheet) |
| Final 1080p60 | `… -q h` (refuses PLACEHOLDER audio) |
| Final 4K master | `… -q k` (refuses PLACEHOLDER audio) |
| Shorts | `… -q h --vertical` (sets `DSANIM_VERTICAL=1`: 9:16 frame, vertical regions, text ×1.25) |

- Iterate at `-ql`. Never run `-qh`/`-qk` until the scene passes review at `-qm`.
- Manim caches partial movie files; do not clear `media/` unless a render is corrupt.
- Expect a 10-minute video at 1080p60 to take an hour or more of CPU time. Final renders run in the background or overnight; never block a review loop on them.

---

## 7. Narration and timing

Manim has no timeline. Timing is derived from audio, never guessed.

**The workflow (script first, voice last):**

1. **Script.** Nitish writes `script.md` (optionally by talking it through into a voice memo; the agent may transcribe that into a *draft* for him to edit). Narration, `[[marks]]`, equations.
2. **Placeholder voice.** `uv run --extra tts python tools/tts_placeholder.py <tier_dir>` generates Kokoro audio per beat into `<audio root>/<concept>/<tier>/placeholder/` with word timings. Calibrate `tts_speed` so placeholder durations match Nitish's pace.
3. **Animate against the placeholder.** Shot list → scenes → review loop (§8). Nitish reviews video *with* the placeholder voice and may still edit wording; because scenes reference beats and equations by id, edited words need no code change — regenerate placeholders and re-render.
4. **Freeze.** Nitish sets `status: frozen`.
5. **Record.** In Audacity, one take per scene, a label at each beat boundary named with the beat key (`s03_b01`, …), *Export Multiple* by labels → `<audio root>/<concept>/<tier>/s03_b01.wav` … (details in `assets/audio/README.md`).
6. **Swap.** Re-render. Recorded files win over placeholders automatically; every beat re-times itself to the real audio. Any beat whose animations no longer fit raises `NarrationOverrun` — shorten the animation, never speed the audio.

**Rules:**
- Audio is **not in git**. Default root is `assets/audio/` (ignored); set `DSANIM_AUDIO_DIR` to keep it on a backed-up drive. Beat 3.2 → `s03_b02.wav`.
- Inside `with self.beat("3.2") as b:` animations must finish within the narration; on exit the scene holds the final state for the rest of the narration plus `TAIL_SILENCE` (0.5 s). So every beat ends on ≥0.5 s of silence.
- Mark times use `<key>.words.json` word timings when present (Kokoro provides them; recorded audio will get them from a forced-alignment tool, `tools/align.py`, still to be built) and otherwise interpolate by word position.
- Placeholder audio is **never shipped**: `-q h`/`-q k` renders abort if any beat uses it.

## 8. The review loop (mandatory — agents cannot see)

You cannot watch the video. Overlapping text, clipped equations, and objects off-screen are invisible to you unless you look. So, for every scene, before reporting it done:

1. Render at `-qm`.
2. Produce the contact sheet: `tools/render.py … -q m --sheet` does both steps; or `uv run python tools/contact_sheet.py <tier>/renders/<Scene>_m.mp4 --every 2`. The sheet always includes the final frame and outlines the safe area in red.
3. **Open and inspect the contact sheet image.** Check: nothing outside the safe area; no text overlapping text; no equation clipped; colours match semantics in §4; every beat's end state matches the shot list.
4. Fix, re-render, re-inspect. Only then report, and include the contact sheet path in the report.

A scene reported "done" without an inspected contact sheet is not done.

---

## 9. Correctness rules

- **Never invent, simplify, or "correct" math.** Every equation on screen must match `script.md` exactly. If the script's equation seems wrong, stop and say so; do not silently fix it.
- **Never invent data.** Real datasets come only from `dsanim.data` loaders over the curated files in `data/` (sources, licences and citations in `data/PROVENANCE.md`; current: UCI Auto MPG, EPA fuel economy 2020+). Synthetic datasets are generated in `src/dsanim/data.py` with a fixed seed and a docstring stating the generating process, so the video can say "here is data drawn from …" truthfully.
- **Never change narration.** Timing, layout, and animation are yours to propose; words are not.
- If a Manim feature is uncertain (API changed between versions, function name unsure), check the installed version's docs (`python -c "import manim; print(manim.__version__)"`) rather than guessing. Common ManimGL-isms that must not appear: `manimlib`, `ShowCreation` (use `Create`), `TextMobject`/`TexMobject` (use `Text`/`MathTex`), `CONFIG` dicts on scenes.

---

## 10. Shorts and multi-format output

- A short is **one beat re-laid-out vertically**, not the long video cropped. The same scene class renders both ways: `tools/render.py --vertical` sets `DSANIM_VERTICAL=1`, and scenes read `self.vertical` / `self.layout` (from `dsanim.layout`) to arrange themselves. `shorts/` holds which beats become Shorts and their caption config — not copies of scene code.
- Shorts get burned-in captions (from `script.md`), larger text (minimum 40px-equivalent at 1080×1920), and open on the state change, not on setup.
- `article.md` is generated from `script.md` (prose form, same equations, same order) and reviewed by Nitish. Static frames from the contact sheet become the article's figures. The article links to the video; the video description links to the article. The canonical URL is Nitish's own site; Medium is syndication.

---

## 11. Definition of done for a topic

- [ ] `script.md` reviewed and frozen by Nitish (equations checked)
- [ ] `shotlist.md` approved
- [ ] Every scene passes the §8 review loop at `-qm`
- [ ] `uv run pytest` passes (including the regression tests added for this topic's new components)
- [ ] Narration recorded; all beats fit their audio
- [ ] Vertical layouts render for the 2–3 beats chosen as shorts
- [ ] Final 1080p60 render assembled with FFmpeg; 4K master queued
- [ ] `article.md` derived and reviewed
- [ ] Thumbnail frame chosen (a single frame from the video that states the misconception)

---

## 12. Working style with Nitish

- Work one scene at a time. Do not generate the whole video in one pass.
- When the shot list is ambiguous, ask one precise question rather than guessing layout.
- Report with: what was rendered, the contact sheet path, what you checked, what you are unsure about. No "looks great" without evidence.
- Prefer boring, reusable code in `src/dsanim/` over clever one-off code in `scenes/`.
- Keep `topics/<NNN>-<slug>/<tier>/NOTES.md` with decisions made and anything that broke, so the next session (or the next agent) picks up without re-learning.

---

## 13. First milestone

Before any curriculum work: produce the 35-second Scene 3 above ("From marginal to conditional") end-to-end — shot list → `dsanim` components (with tests + gallery scenes) → code → `-qm` render → inspected contact sheet → `-qh` render. It lives at `topics/030-regression-is-conditional-distribution/L1/`, uses `dsanim.data.auto_mpg()` (weight in kg), and starts once Nitish has written that tier's `script.md`. This pilot validates the workflow, the render times, and the visual language. Nothing else starts until it looks right.

---

## 14. Testing (mandatory)

Every piece of code ships with tests in the same change. Nitish's rule: **tests for all code, regression tests for every major feature, and smoke tests.**

| Layer | Folder | Marker | What |
|---|---|---|---|
| Unit | `tests/unit/` | — | pure logic: palette, layout, parser, narration, data, each tool |
| Regression | `tests/regression/` | `regression` | pins a major feature against a golden/known result: parsed-script snapshots, beat timing vs audio, style-sheet golden frames |
| Smoke | `tests/smoke/` | `smoke` | does the toolchain work at all: imports, fonts, TeX, tool CLIs, a real `-ql` render in both orientations, TTS |

- Anything that renders or runs TTS is also marked `slow`. Fast loop: `uv run pytest -m "not slow"` (~1 s). Before reporting anything done: `uv run pytest` (~20 s; `uv run --extra tts pytest` to include the TTS smoke test).
- A new `dsanim` component = unit tests for its geometry/logic + a `gallery/` scene + (for major components) a golden-frame regression test.
- Goldens live in `tests/regression/golden/`. Regenerate only for an **intentional** change: `DSANIM_UPDATE_GOLDEN=1 uv run pytest <test>`, then open the new PNG/JSON and check it before committing.
- A failing test is reported as failing, with its output. Never delete or loosen a test to make it pass without saying so.

---

## 15. Agent tooling and keeping docs current

- **Hooks** (`.claude/settings.json`): after every edit to a `.py` file, `tools/lint_scenes.py --hook` runs and blocks on violations (ManimGL-isms, hex colours outside `palette.py`, inline LaTeX or Manim colour constants in topic scenes). Edits to any `script.md` require Nitish's approval.
- **Skills** (`.claude/skills/`): `new-topic`, `draft-shotlist`, `build-scene`, `render-review`, `narration`. They encode §5–§8 step by step; Codex and other agents should follow the same steps from this file.
- **Keep docs current.** When a convention, tool or structure changes, update this file (and the nested `AGENTS.md`), log it in `channel/decisions.md`, and keep `.claude/` skills consistent — in the same change.
