# Animated data-science channel — production repo

Videos that teach data science, ML and econometrics from the real foundations, animated with
[Manim Community](https://www.manim.community/). No presenter; Nitish writes and narrates,
coding agents build the animation, the tools here turn scripts into finished videos, Shorts
and subtitles.

**Rules for agents live in [AGENTS.md](AGENTS.md).** This file is for humans.

## Setup (macOS, Apple Silicon)

```bash
./tools/bootstrap.sh          # brew: cairo pango ffmpeg fonts inkscape kdenlive; TinyTeX; uv sync
uv run pytest -m "not slow"   # ~2 s: everything imports and the tools work
uv run pytest                 # ~1 min: real renders, TeX, goldens
```

## The three commands you will actually use

```bash
uv run python tools/status.py   topics/030-regression-is-conditional-distribution/L1
uv run python tools/pipeline.py topics/030-regression-is-conditional-distribution/L1 --qualities l m h
uv run python tools/render.py   topics/.../L1/scenes/s03_conditional.py Scene03 -q m --sheet
```

`status.py` tells you what is missing and **who** owes it (NITISH / CODE / AGENT).
`pipeline.py` renders every scene at 480p, 720p and 1080p, assembles each into one video with
YouTube chapters and an SRT, and cuts the vertical chunks declared in `shorts/chunks.yaml`.
`render.py --sheet` is the review loop for one scene (a grid of frames to look at).

## What you provide, in order

1. `script.md` in the tier folder — narration in beats, `[[marks]]`, equations (`AGENTS.md §5.1`).
2. Approval of the drafted `shotlist.md` (`Status: approved`).
3. `status: frozen` in the script once the words are final.
4. Narration: one WAV per beat from Audacity into `assets/audio/<concept>/<tier>/`
   (`assets/audio/README.md`). Until then the pipeline uses a watermarked placeholder voice.
5. `shorts/chunks.yaml` (which beats become vertical chunks), `publish/description.md`, a
   thumbnail frame.

Everything else — placeholder voice, renders, contact sheets, chapters, subtitles, chunks,
manifests — is produced by the tools. Two ways to run them are described in
[channel/pipeline.md](channel/pipeline.md): deterministic (just the tools) and agent-assisted
(an agent reviews frames and adjusts).

## Layout

`src/dsanim/` the visual language · `topics/<NNN-concept>/<L1|L2|L3>/` one video per tier ·
`gallery/` component review scenes · `tools/` the pipeline · `tests/` unit / regression / smoke ·
`channel/` curriculum, decisions, pipeline doc · `data/` curated datasets with provenance.
