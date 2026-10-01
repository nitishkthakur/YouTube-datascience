"""Regression for the cache bug: a second render of an unchanged scene into the same media
dir must still carry the narration of every beat and produce identical beat timings, and the
video must hold exactly the frames the sidecar implies."""

import json
import subprocess

import pytest

from conftest import FIXTURES, render_env, run_manim, write_tone

SCENE = FIXTURES / "topic/L1/scenes/s01_timing.py"
pytestmark = [pytest.mark.regression, pytest.mark.slow]


def mean_volume_db(video, start, length) -> float:
    r = subprocess.run(["ffmpeg", "-ss", f"{start:.3f}", "-t", f"{length:.3f}", "-i", str(video),
                        "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True)
    line = next(l for l in r.stderr.splitlines() if "mean_volume" in l)
    return float(line.split("mean_volume:")[1].split("dB")[0])


def frame_count(video) -> int:
    r = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v",
                        "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(video)],
                       capture_output=True, text=True)
    return int(r.stdout.strip())


def test_second_render_keeps_narration_and_timings(tmp_path):
    audio = tmp_path / "audio"
    write_tone(audio / "fixture-topic/L1/s01_b01.wav", 1.2)
    write_tone(audio / "fixture-topic/L1/s01_b02.wav", 1.0)
    media = tmp_path / "media"
    env = render_env(DSANIM_AUDIO_DIR=audio)
    sidecars, videos = [], []
    for _ in range(2):
        r = run_manim(SCENE, "Scene01", "twice", media, env)
        assert r.returncode == 0, r.stderr[-2000:]
        sidecars.append(json.loads((media / "timings" / "twice.json").read_text()))
        videos.append(next(media.glob("videos/**/twice.mp4")))
    assert sidecars[0]["beats"] == sidecars[1]["beats"]
    side = sidecars[1]
    for beat in side["beats"]:
        # the tone (-20 dBFS) is audible inside the beat's speech window on the second render
        assert mean_volume_db(videos[1], beat["start"] + 0.1, 0.8) > -40, beat["id"]
    assert frame_count(videos[1]) == round(side["duration"] * side["frame_rate"])
