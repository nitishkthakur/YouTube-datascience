"""Visual regression: the final frame of the gallery style sheet at -ql.

Catches accidental changes to palette, fonts, TeX template, layout regions. Intentional
visual changes: regenerate with DSANIM_UPDATE_GOLDEN=1 and LOOK at the new PNG first.
"""

import os
import subprocess
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from conftest import ROOT, render_env, run_manim

GOLDEN = Path(__file__).parent / "golden"
pytestmark = [pytest.mark.regression, pytest.mark.slow]
TOLERANCE = 2.0  # mean absolute difference per channel, 0-255


@pytest.mark.parametrize("vertical", [False, True])
def test_style_sheet_last_frame(tmp_path, vertical):
    tag = "v" if vertical else "h"
    env = render_env(DSANIM_AUDIO_DIR=tmp_path / "no-audio", DSANIM_VERTICAL=int(vertical))
    r = run_manim(ROOT / "gallery/style_sheet.py", "StyleSheet", f"ss_{tag}", tmp_path / "media", env)
    assert r.returncode == 0, r.stderr[-2000:]
    video = next((tmp_path / "media").glob(f"videos/**/ss_{tag}.mp4"))
    frame = tmp_path / "last.png"
    subprocess.run(["ffmpeg", "-v", "error", "-sseof", "-0.1", "-i", str(video), "-frames:v", "1",
                    "-update", "1", str(frame)], check=True)
    got = np.asarray(Image.open(frame).convert("RGB"), dtype=float)

    golden = GOLDEN / f"style_sheet_last_{tag}.png"
    if os.environ.get("DSANIM_UPDATE_GOLDEN") == "1" or not golden.exists():
        Image.open(frame).save(golden)
        if os.environ.get("DSANIM_UPDATE_GOLDEN") != "1":
            pytest.skip(f"created golden {golden.name}; inspect it, then re-run")
    want = np.asarray(Image.open(golden).convert("RGB"), dtype=float)
    assert got.shape == want.shape
    assert np.abs(got - want).mean() < TOLERANCE
