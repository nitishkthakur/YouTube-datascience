"""Shared fixtures. Test layers:
  tests/unit        pure logic, fast
  tests/regression  golden/known-result checks for major features   (@pytest.mark.regression)
  tests/smoke       does the toolchain work end to end at all        (@pytest.mark.smoke)
Anything that renders video or runs TTS is also @pytest.mark.slow.
Quick loop: `uv run pytest -m "not slow"`. Before reporting work done: `uv run pytest`.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
TINYTEX = Path.home() / "Library" / "TinyTeX" / "bin" / "universal-darwin"


def pytest_configure(config):
    # In-process renders (e.g. MathTex) need xelatex even if the shell profile wasn't loaded.
    if TINYTEX.exists() and str(TINYTEX) not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{os.environ.get('PATH', '')}:{TINYTEX}"


def load_tool(name: str):
    """Import tools/<name>.py as a module (tools/ is scripts, not a package)."""
    spec = importlib.util.spec_from_file_location(f"tools_{name}", ROOT / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_tone(path: Path, seconds: float, sr: int = 24_000) -> Path:
    """A quiet sine tone standing in for narration of a known length."""
    path.parent.mkdir(parents=True, exist_ok=True)
    t = np.arange(int(seconds * sr)) / sr
    sf.write(path, 0.1 * np.sin(2 * np.pi * 220 * t), sr)
    return path


def render_env(**extra) -> dict:
    env = dict(os.environ)
    if TINYTEX.exists():
        env["PATH"] = f"{env.get('PATH', '')}:{TINYTEX}"
    env.update({k: str(v) for k, v in extra.items()})
    return env


def run_manim(scene_file: Path, scene: str, out_name: str, media: Path, env: dict,
              quality: str = "l") -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-m", "manim", "render", f"-q{quality}", "--media_dir", str(media),
           "-o", out_name, str(scene_file), scene]
    return subprocess.run(cmd, env=env, cwd=ROOT, capture_output=True, text=True)


def video_duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                          "default=nw=1:nk=1", str(path)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


@pytest.fixture
def audio_dir(tmp_path, monkeypatch) -> Path:
    """An isolated DSANIM_AUDIO_DIR for the test."""
    d = tmp_path / "audio"
    d.mkdir()
    monkeypatch.setenv("DSANIM_AUDIO_DIR", str(d))
    return d


@pytest.fixture
def fixture_script() -> Path:
    return FIXTURES / "topic" / "L1" / "script.md"
