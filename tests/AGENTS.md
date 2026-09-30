# tests — unit, regression, smoke (root AGENTS.md §14)

- `unit/` fast pure-logic tests; `regression/` goldens and known-result checks for major
  features (`@pytest.mark.regression`); `smoke/` "does it work at all" (`@pytest.mark.smoke`).
  Renders/TTS are also `@pytest.mark.slow`.
- `uv run pytest -m "not slow"` while iterating; `uv run pytest` before reporting done.
- Helpers in `conftest.py`: `load_tool`, `write_tone` (audio of known length),
  `run_manim`, `render_env`, `video_duration`, fixtures `audio_dir`, `fixture_script`.
- `fixtures/topic/L1/` is a miniature topic (script + scenes) for parser and timing tests.
  Extend it rather than pointing tests at real topics, which change.
- Goldens: `regression/golden/`. Regenerate only for intended changes with
  `DSANIM_UPDATE_GOLDEN=1`, and inspect the result.
- Never weaken or delete a test to get green without telling Nitish.
