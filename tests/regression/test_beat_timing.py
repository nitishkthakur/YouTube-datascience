"""Regression: the narration-timing contract of DSScene.beat() (AGENTS.md §7).

- a beat lasts exactly its audio + TAIL_SILENCE when the animations fit;
- animations longer than the audio raise NarrationOverrun (never speed up audio);
- final renders refuse placeholder audio;
- wait_until([[mark]]) lands on the mark's word timing.
"""

import json

import pytest

from conftest import FIXTURES, render_env, run_manim, video_duration, write_tone
from dsanim import palette as P

SCENE = FIXTURES / "topic/L1/scenes/timing_scene.py"
pytestmark = [pytest.mark.regression, pytest.mark.slow]


def _find(media, name):
    hits = list(media.glob(f"videos/**/{name}.mp4"))
    assert hits, f"{name}.mp4 not rendered"
    return hits[0]


def test_beat_duration_is_audio_plus_tail(tmp_path):
    audio = tmp_path / "audio"
    write_tone(audio / "fixture-topic/L1/s01_b01.wav", 1.5)
    r = run_manim(SCENE, "FitsBeat", "fits", tmp_path / "media", render_env(DSANIM_AUDIO_DIR=audio))
    assert r.returncode == 0, r.stderr[-2000:]
    assert video_duration(_find(tmp_path / "media", "fits")) == pytest.approx(
        1.5 + P.TAIL_SILENCE, abs=0.1)


def test_overrun_raises(tmp_path):
    audio = tmp_path / "audio"
    write_tone(audio / "fixture-topic/L1/s01_b01.wav", 1.0)
    r = run_manim(SCENE, "OverrunsBeat", "over", tmp_path / "media", render_env(DSANIM_AUDIO_DIR=audio))
    assert r.returncode != 0
    assert "NarrationOverrun" in r.stdout + r.stderr


def test_final_render_refuses_placeholder(tmp_path):
    audio = tmp_path / "audio"
    write_tone(audio / "fixture-topic/L1/placeholder/s01_b01.wav", 1.5)
    r = run_manim(SCENE, "FitsBeat", "final", tmp_path / "media",
                  render_env(DSANIM_AUDIO_DIR=audio, DSANIM_FINAL=1))
    assert r.returncode != 0
    assert "PLACEHOLDER" in r.stdout + r.stderr


def test_wait_until_mark_uses_word_timings(tmp_path):
    audio = tmp_path / "audio"
    wav = write_tone(audio / "fixture-topic/L1/s01_b01.wav", 4.0)
    words = ["One", "two", "three", "four", "five", "six."]
    wav.with_suffix(".words.json").write_text(json.dumps(
        [{"word": w, "start": 0.5 * i, "end": 0.5 * i + 0.4} for i, w in enumerate(words)]))
    # mark [[go]] fires at word 4 -> 1.5 s; then 0.2 s animation; beat still ends at 4.0 + tail
    r = run_manim(SCENE, "WaitsForMark", "mark", tmp_path / "media", render_env(DSANIM_AUDIO_DIR=audio))
    assert r.returncode == 0, r.stderr[-2000:]
    assert video_duration(_find(tmp_path / "media", "mark")) == pytest.approx(4.0 + P.TAIL_SILENCE, abs=0.1)


def test_extend_allows_silent_visual_time(tmp_path):
    # 1.0 s speech, 2.0 s animation, extend 1.5 -> beat ends at 2.0 + tail
    audio = tmp_path / "audio"
    write_tone(audio / "fixture-topic/L1/s01_b01.wav", 1.0)
    r = run_manim(SCENE, "ExtendsBeat", "ext", tmp_path / "media", render_env(DSANIM_AUDIO_DIR=audio))
    assert r.returncode == 0, r.stderr[-2000:]
    assert video_duration(_find(tmp_path / "media", "ext")) == pytest.approx(
        2.0 + P.TAIL_SILENCE, abs=0.1)


def test_extend_budget_is_enforced(tmp_path):
    # 1.0 s speech + 0.5 s extend < 2.0 s animation -> overrun
    audio = tmp_path / "audio"
    write_tone(audio / "fixture-topic/L1/s01_b01.wav", 1.0)
    r = run_manim(SCENE, "ExtendTooSmall", "ext2", tmp_path / "media", render_env(DSANIM_AUDIO_DIR=audio))
    assert r.returncode != 0 and "NarrationOverrun" in r.stdout + r.stderr


def test_safe_area_violation_warns_while_iterating(tmp_path):
    r = run_manim(SCENE, "LeavesSafeArea", "unsafe", tmp_path / "media",
                  render_env(DSANIM_AUDIO_DIR=tmp_path / "none"))
    assert r.returncode == 0, r.stderr[-2000:]
    assert "outside safe area" in r.stdout + r.stderr


def test_safe_area_violation_fails_final_render(tmp_path):
    r = run_manim(SCENE, "LeavesSafeArea", "unsafe_final", tmp_path / "media",
                  render_env(DSANIM_AUDIO_DIR=tmp_path / "none", DSANIM_FINAL=1))
    assert r.returncode != 0 and "SafeAreaViolation" in r.stdout + r.stderr


def test_invisible_and_inside_mobjects_pass_safe_area(tmp_path):
    r = run_manim(SCENE, "StaysInSafeArea", "safe", tmp_path / "media",
                  render_env(DSANIM_AUDIO_DIR=tmp_path / "none"))
    assert r.returncode == 0 and "outside safe area" not in r.stdout + r.stderr
