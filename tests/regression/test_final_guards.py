"""Final renders refuse what must never ship: missing narration, stale recordings."""

import json
import shutil

import pytest

from conftest import FIXTURES, load_tool, render_env, run_manim, write_tone

pytestmark = [pytest.mark.regression, pytest.mark.slow]
SCENE = FIXTURES / "topic/L1/scenes/timing_scene.py"


def test_missing_narration_fails_a_final_render(tmp_path):
    r = run_manim(SCENE, "FitsBeat", "nonar", tmp_path / "media",
                  render_env(DSANIM_AUDIO_DIR=tmp_path / "none", DSANIM_FINAL=1))
    assert r.returncode != 0 and "no narration" in r.stdout + r.stderr


def test_stale_recording_fails_a_final_render(tmp_path, monkeypatch):
    tier = tmp_path / "topic" / "L1"
    shutil.copytree(FIXTURES / "topic" / "L1", tier, ignore=shutil.ignore_patterns("renders"))
    audio = tmp_path / "audio"
    monkeypatch.setenv("DSANIM_AUDIO_DIR", str(audio))
    write_tone(audio / "fixture-topic/L1/s01_b01.wav", 1.5)
    load_tool("audio_manifest").register(tier)
    env = render_env(DSANIM_AUDIO_DIR=audio, DSANIM_FINAL=1)
    r = run_manim(tier / "scenes" / "timing_scene.py", "FitsBeat", "ok", tmp_path / "media", env)
    assert r.returncode == 0, r.stderr[-2000:]
    script = tier / "script.md"
    script.write_text(script.read_text().replace("One two three", "One two THREE"))
    r = run_manim(tier / "scenes" / "timing_scene.py", "FitsBeat", "stale", tmp_path / "media", env)
    assert r.returncode != 0 and "RecordingStale" in r.stdout + r.stderr
