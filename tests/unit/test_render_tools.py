import subprocess
import sys
from pathlib import Path

from PIL import Image

from conftest import ROOT, load_tool

render = load_tool("render")


def test_renders_dir_for_topic_and_gallery():
    assert render.renders_dir(ROOT / "topics/030-x/L1/scenes/s03.py") == ROOT / "topics/030-x/L1/renders"
    assert render.renders_dir(ROOT / "topics/030-x/L1/shorts/s03.py") == ROOT / "topics/030-x/L1/renders"
    assert render.renders_dir(ROOT / "gallery/style_sheet.py") == ROOT / "gallery/renders"


def test_contact_sheet_grid_from_synthetic_video(tmp_path):
    video = tmp_path / "v.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=640x360:rate=15",
                    "-t", "5", "-pix_fmt", "yuv420p", str(video)], check=True)
    r = subprocess.run([sys.executable, str(ROOT / "tools/contact_sheet.py"), str(video),
                        "--every", "2", "--cols", "2"], check=True, capture_output=True, text=True)
    sheet = Image.open(video.with_suffix(".sheet.png"))
    # frames at 0, 2, 4 + the final frame -> 4 tiles -> 2x2 grid of 640x(360+28) tiles, 6 px gutters
    assert "(4 frames" in r.stdout
    assert sheet.size == (2 * 640 + 3 * 6, 2 * (360 + 28) + 3 * 6)
