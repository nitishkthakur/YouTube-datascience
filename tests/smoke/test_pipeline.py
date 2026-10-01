"""Smoke: the deterministic pipeline end to end on the fixture tier at 480p.

Copies the fixture tier to a temp dir (renders must not pollute the repo), gives one beat a
real audio file and leaves the rest silent, declares one vertical chunk, then runs
tools/pipeline.py and checks every artefact it promises.
"""

import json
import shutil
import subprocess
import sys

import pytest

from conftest import FIXTURES, ROOT, video_duration, write_tone

pytestmark = [pytest.mark.smoke, pytest.mark.slow]


def test_pipeline_fixture_tier(tmp_path, monkeypatch):
    tier = tmp_path / "topic" / "L1"
    shutil.copytree(FIXTURES / "topic" / "L1", tier, ignore=shutil.ignore_patterns("renders"))
    audio = tmp_path / "audio"
    write_tone(audio / "fixture-topic/L1/s01_b01.wav", 1.5)
    (tier / "shorts").mkdir(exist_ok=True)
    (tier / "shorts" / "chunks.yaml").write_text(
        "chunks:\n  - name: beat-two\n    scenes: [s01_timing.py]\n    from_beat: '1.2'\n")
    env = {**dict(__import__("os").environ), "DSANIM_AUDIO_DIR": str(audio)}

    r = subprocess.run([sys.executable, str(ROOT / "tools/pipeline.py"), str(tier),
                        "--qualities", "l", "--jobs", "2"], env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-3000:]

    renders, publish = tier / "renders", tier / "publish"
    manifest = json.loads((renders / "manifest_l.json").read_text())
    assert [s["class"] for s in manifest["scenes"]] == ["Scene01", "Scene02"]
    total = sum(s["duration"] for s in manifest["scenes"])
    assembled = renders / "fixture-topic_L1_l.mp4"
    assert video_duration(assembled) == pytest.approx(total, abs=0.3)

    chapters = (publish / "chapters.txt").read_text().splitlines()
    assert chapters[0] == "0:00 Timing" and chapters[1].endswith("Second")
    srt = (publish / "subtitles.srt").read_text()
    assert "One two three four five six." in srt and "-->" in srt

    short = renders / "shorts" / "beat-two_l.mp4"
    beats = json.loads((renders / "Scene01_l_v.beats.json").read_text())["beats"]
    b12 = next(b for b in beats if b["id"] == "1.2")
    assert video_duration(short) == pytest.approx(b12["end"] - b12["start"], abs=0.3)
    assert "next" in r.stdout and "narration recorded" in r.stdout
    manifest_pub = json.loads((publish / "manifest_l.json").read_text())
    out_lufs = manifest_pub["loudness"]["output_lufs"]
    assert out_lufs is None or out_lufs == pytest.approx(-14.0, abs=2.5)   # one 1.5 s tone in 12 s
    assert len(manifest_pub["seams"]) == 1
