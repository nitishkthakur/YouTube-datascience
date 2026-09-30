"""Smoke: Kokoro placeholder narration generates audio + word timings (needs `--extra tts`)."""

import json
import subprocess
import sys

import pytest
import soundfile as sf

from conftest import FIXTURES, ROOT, render_env

pytestmark = [pytest.mark.smoke, pytest.mark.slow]


def test_placeholder_audio_and_word_timings(tmp_path):
    pytest.importorskip("kokoro")
    env = render_env(DSANIM_AUDIO_DIR=tmp_path)
    r = subprocess.run([sys.executable, str(ROOT / "tools/tts_placeholder.py"),
                        str(FIXTURES / "topic/L1"), "--beats", "1.1"],
                       env=env, capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    wav = tmp_path / "fixture-topic/L1/placeholder/s01_b01.wav"
    assert 1.0 < sf.info(str(wav)).duration < 10.0
    words = json.loads(wav.with_suffix(".words.json").read_text())
    assert [w["word"] for w in words][:3] == ["One", "two", "three"]
    assert all(a["start"] <= b["start"] for a, b in zip(words, words[1:]))
