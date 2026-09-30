import json
import subprocess

import pytest

from conftest import FIXTURES, load_tool
from dsanim.script import parse

assemble = load_tool("assemble")


def synth(path, seconds, audio: bool):
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc=size=320x180:rate=15",
           "-t", str(seconds)]
    if audio:
        cmd += ["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=24000", "-t", str(seconds),
                "-c:a", "aac"]
    cmd += ["-pix_fmt", "yuv420p", str(path)]
    subprocess.run(cmd, check=True)
    return path


@pytest.mark.parametrize("t,s", [(0, "0:00"), (65, "1:05"), (3600, "1:00:00"), (599.6, "10:00")])
def test_chapter_stamp(t, s):
    assert assemble.chapter_stamp(t) == s


def test_normalise_adds_audio_and_concat_keeps_total_duration(tmp_path):
    a = synth(tmp_path / "a.mp4", 2, audio=True)
    b = synth(tmp_path / "b.mp4", 3, audio=False)
    assert assemble.has_audio(a) and not assemble.has_audio(b)
    parts = [assemble.normalise(a, tmp_path / "a.n.mp4"), assemble.normalise(b, tmp_path / "b.n.mp4")]
    assert all(assemble.has_audio(p) for p in parts)
    out = assemble.concat(parts, tmp_path / "out.mp4")
    assert assemble.duration(out) == pytest.approx(5.0, abs=0.2)


def test_chapters_and_subtitles_from_sidecars(tmp_path):
    script = parse(FIXTURES / "topic/L1/script.md")
    sidecar = tmp_path / "s.json"
    sidecar.write_text(json.dumps({"beats": [
        {"start": 1.0, "captions": [{"text": "one", "start": 0.0, "end": 0.5},
                                    {"text": "two", "start": 0.5, "end": 1.0}]}]}))
    scenes = [{"scene_number": 1, "class": "Scene01", "beats_json": str(sidecar)},
              {"scene_number": 2, "class": "Scene02", "beats_json": None},
              {"scene_number": 9, "class": "Unknown", "beats_json": None}]
    chapters, subs = assemble.chapters_and_subtitles(script, scenes, [0.0, 10.0, 20.0])
    assert chapters == ["0:00 Timing", "0:10 Second", "0:20 Unknown"]
    assert subs == [(1.0, 1.5, "one"), (1.5, 2.0, "two")]


def test_missing_manifest_is_a_clear_error(tmp_path):
    with pytest.raises(SystemExit, match="render_all"):
        assemble.main([str(tmp_path), "-q", "l"])
