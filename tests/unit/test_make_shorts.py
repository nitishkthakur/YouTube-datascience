import json
import subprocess

import pytest

from conftest import load_tool

make_shorts = load_tool("make_shorts")


def test_load_chunks_validates(tmp_path):
    (tmp_path / "shorts").mkdir()
    assert make_shorts.load_chunks(tmp_path) == []
    (tmp_path / "shorts" / "chunks.yaml").write_text("chunks:\n  - name: x\n")
    with pytest.raises(SystemExit, match="scenes"):
        make_shorts.load_chunks(tmp_path)
    (tmp_path / "shorts" / "chunks.yaml").write_text(
        "chunks:\n  - name: x\n    scenes: [s01_a.py]\n    from_beat: '1.2'\n")
    assert make_shorts.load_chunks(tmp_path)[0]["from_beat"] == "1.2"


def test_beat_window(tmp_path):
    sc = tmp_path / "s.beats.json"
    sc.write_text(json.dumps({"beats": [{"id": "1.1", "start": 0.0, "end": 2.5},
                                        {"id": "1.2", "start": 2.5, "end": 4.0}]}))
    assert make_shorts.beat_window(sc, None, None) == (None, None)
    assert make_shorts.beat_window(sc, "1.2", None) == (2.5, None)
    assert make_shorts.beat_window(sc, None, "1.1") == (None, 2.5)
    with pytest.raises(KeyError):
        make_shorts.beat_window(sc, "9.9", None)


def test_cut_and_concat(tmp_path):
    src = tmp_path / "src.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=180x320:rate=15",
                    "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000", "-t", "4",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", str(src)], check=True)
    a = make_shorts.cut(src, tmp_path / "a.mp4", 1.0, 3.0)
    b = make_shorts.cut(src, tmp_path / "b.mp4", None, 1.0)
    out = make_shorts.concat([a, b], tmp_path / "out.mp4")
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                            "default=nw=1:nk=1", str(out)], capture_output=True, text=True)
    assert float(probe.stdout) == pytest.approx(3.0, abs=0.15)
