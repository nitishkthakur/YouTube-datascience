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

## Rules
- Every tool gets tests (`tests/unit/` for logic, `tests/smoke/` that it runs). Factor logic
  into functions that tests can import (`conftest.load_tool("name")`); keep `main()` thin.
- Tools must work without the user's shell profile (explicit PATHs, no reliance on `~/.zshrc`).
- Planned, not yet built: `align.py` (forced alignment of recorded audio → `.words.json`),
  `assemble.py` (FFmpeg concat of scene renders + audio into the final video).
  Build them when first needed, with tests.
