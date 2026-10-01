"""assemble.finalize: loudness to -14 LUFS, BT.709 tags, optional re-encode."""

import subprocess

import pytest

from conftest import load_tool

assemble = load_tool("assemble")


def quiet_video(path, seconds=4):
    # a sine at -30 dBFS: far quieter than the -14 LUFS target
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=320x180:rate=15",
                    "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000", "-t", str(seconds),
                    "-af", "volume=-30dB", "-pix_fmt", "yuv420p", "-c:a", "aac", str(path)], check=True)
    return path


def probe_color(path) -> str:
    return subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                           "stream=color_space,color_primaries,color_transfer,color_range", "-of", "csv=p=0",
                           str(path)], capture_output=True, text=True).stdout.strip()


@pytest.mark.parametrize("reencode", [False, True])
def test_finalize_normalises_loudness_and_tags_colour(tmp_path, reencode):
    src = quiet_video(tmp_path / "src.mp4")
    before = assemble.measure_loudness(src)
    assert float(before["input_i"]) < -20
    result = assemble.finalize(src, tmp_path / "out.mp4", reencode=reencode)
    assert result["reencoded"] is reencode
    assert result["output_lufs"] == pytest.approx(-14.0, abs=1.5)
    assert "bt709" in probe_color(tmp_path / "out.mp4")
    assert assemble.duration(tmp_path / "out.mp4") == pytest.approx(4.0, abs=0.2)
