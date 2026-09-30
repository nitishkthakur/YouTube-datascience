# tools — command-line scripts

Scripts, not a package. Run with `uv run python tools/<name>.py …` from the repo root.
Each has a docstring with usage; keep it accurate.

| Tool | Purpose |
|---|---|
| `render.py` | the only way to render: TinyTeX PATH, `--vertical`, final-render placeholder guard, copies to `<tier>/renders/`, `--sheet` |
| `contact_sheet.py` | frame grid (+ final frame, + red safe-area outline) for agents to inspect |
| `check_script.py` | validate `script.md`; per-beat words/duration/audio/marks/equations; `--scenes` cross-checks ids used in scene code |
| `lint_scenes.py` | rule checks; `--hook` mode is wired into `.claude/settings.json` |
| `tts_placeholder.py` | Kokoro placeholder narration + `.words.json` (needs `--extra tts`) |
| `new_topic.py` | scaffold concept/tier from `topics/_template` |
| `fetch_data.py` | re-download real datasets, rewrite curated copies in `data/` |
| `render_all.py` | every `sNN_*.py` scene of a tier at one quality (16:9 or `--vertical`), optional `--jobs`; writes `renders/manifest_<q>[_v].json` |
| `assemble.py` | concat a tier's scene renders (audio normalised) → one video + `publish/chapters.txt` + `publish/subtitles.srt` + `publish/manifest.json` |
| `make_shorts.py` | vertical chunks from `shorts/chunks.yaml` (scenes, optional beat range) → `renders/shorts/<name>_<q>.mp4` |
| `status.py` | readiness report: what NITISH / CODE / AGENT still owe for a tier |
| `pipeline.py` | the deterministic one-shot: status → (placeholders) → render all qualities → assemble → shorts → status |

## Rules
- Every tool gets tests (`tests/unit/` for logic, `tests/smoke/` that it runs). Factor logic
  into functions that tests can import (`conftest.load_tool("name")`); keep `main()` thin.
- Tools must work without the user's shell profile (explicit PATHs, no reliance on `~/.zshrc`).
- Planned, not yet built: `align.py` (forced alignment of recorded audio → `.words.json`),
  `thumbnail.py` (candidate frames). Build them when first needed, with tests.
