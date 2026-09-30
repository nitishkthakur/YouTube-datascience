"""Regression: the narration-timing contract of DSScene.beat() (AGENTS.md §7).

- a beat lasts exactly its audio + TAIL_SILENCE when the animations fit;
- animations longer than the audio raise NarrationOverrun (never speed up audio);
- final renders refuse placeholder audio;
- wait_until([[mark]]) lands on the mark's word timing.
"""

import json
import shutil
import subprocess

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
    # mark [[go]] = word 4 starts at 1.5 s: the scene must hold until then, and say so in the sidecar
    r = run_manim(SCENE, "WaitsForMark", "mark", tmp_path / "media", render_env(DSANIM_AUDIO_DIR=audio))
    assert r.returncode == 0, r.stderr[-2000:]
    side = json.loads((tmp_path / "media" / "timings" / "mark.json").read_text())
    go = side["beats"][0]["marks"]["go"]
    assert go["planned"] == pytest.approx(1.5) and go["hit"] == pytest.approx(1.5, abs=1 / 15)
    assert video_duration(_find(tmp_path / "media", "mark")) == pytest.approx(4.0 + P.TAIL_SILENCE, abs=0.1)


def test_overrun_only_warns_without_real_audio(tmp_path):
    # estimate: 6 words at 120 wpm = 3.0 s; OverrunsBeat animates 3.0 s + tail -> no overrun;
    # ExtendTooSmall would overrun a 1 s recording, but with an estimate it must only warn.
    r = run_manim(SCENE, "OverrunsBeat", "est", tmp_path / "media",
                  render_env(DSANIM_AUDIO_DIR=tmp_path / "none"))
    assert r.returncode == 0, r.stderr[-2000:]


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


def test_timings_sidecar_is_written(tmp_path):
    audio = tmp_path / "audio"
    write_tone(audio / "fixture-topic/L1/s01_b01.wav", 1.5)
    r = run_manim(SCENE, "FitsBeat", "side", tmp_path / "media", render_env(DSANIM_AUDIO_DIR=audio))
    assert r.returncode == 0, r.stderr[-2000:]
    side = json.loads((tmp_path / "media" / "timings" / "side.json").read_text())
    beat = side["beats"][0]
    assert beat["id"] == "1.1" and beat["audio"] == "recorded" and len(beat["audio_sha256"]) == 64
    assert beat["start"] == 0.0 and beat["speech_end"] == pytest.approx(1.5, abs=0.01)
    assert beat["end"] == pytest.approx(side["duration"], abs=0.01)
    assert beat["captions"][0]["text"].startswith("One two")


def test_vertical_render_burns_captions(tmp_path):
    from PIL import Image
    import numpy as np
    r = run_manim(SCENE, "FitsBeat", "cap", tmp_path / "media",
                  render_env(DSANIM_AUDIO_DIR=tmp_path / "none", DSANIM_VERTICAL=1))
    assert r.returncode == 0, r.stderr[-2000:]
    video = next((tmp_path / "media").glob("videos/**/cap.mp4"))
    frame = tmp_path / "f.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1.0", "-i", str(video), "-frames:v", "1",
                    str(frame)], check=True)
    im = np.asarray(Image.open(frame).convert("L"))
    h = im.shape[0]
    band = im[int(h * 0.85):int(h * 0.95), :]   # the caption band (bottom 10% of the safe area)
    assert band.max() > 150, "no bright caption pixels in the caption band"


def test_final_render_requires_frozen_script(tmp_path):
    tier = tmp_path / "topic" / "L1"
    shutil.copytree(FIXTURES / "topic" / "L1", tier, ignore=shutil.ignore_patterns("renders"))
    script = tier / "script.md"
    script.write_text(script.read_text().replace("status: frozen", "status: draft"))
    scene = tier / "scenes" / "timing_scene.py"
    env = render_env(DSANIM_AUDIO_DIR=tmp_path / "none", DSANIM_FINAL=1)
    r = run_manim(scene, "FitsBeat", "draft", tmp_path / "media", env)
    assert r.returncode != 0 and "ScriptNotFrozen" in r.stdout + r.stderr
    env["DSANIM_ALLOW_PLACEHOLDER"] = "1"
    r = run_manim(scene, "FitsBeat", "draft_ok", tmp_path / "media", env)
    assert r.returncode == 0, r.stderr[-2000:]


def test_placeholder_test_render_is_watermarked(tmp_path):
    from PIL import Image
    import numpy as np
    audio = tmp_path / "audio"
    write_tone(audio / "fixture-topic/L1/placeholder/s01_b01.wav", 1.5)
    env = render_env(DSANIM_AUDIO_DIR=audio, DSANIM_FINAL=1, DSANIM_ALLOW_PLACEHOLDER=1)
    r = run_manim(SCENE, "FitsBeat", "wm", tmp_path / "media", env)
    assert r.returncode == 0, r.stderr[-2000:]
    video = next((tmp_path / "media").glob("videos/**/wm.mp4"))
    frame = tmp_path / "f.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1.0", "-i", str(video), "-frames:v", "1",
                    str(frame)], check=True)
    im = np.asarray(Image.open(frame).convert("RGB")).astype(int)
    h, w, _ = im.shape
    corner = im[int(h * 0.85):int(h * 0.97), int(w * 0.5):int(w * 0.97)]
    coral = (abs(corner[..., 0] - 0xF8) < 40) & (abs(corner[..., 1] - 0x71) < 40) & (abs(corner[..., 2] - 0x71) < 40)
    assert coral.sum() > 20, "no watermark pixels in the bottom-right corner"
