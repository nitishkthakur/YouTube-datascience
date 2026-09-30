"""Process environment for renders: the one place that knows where TeX lives.

Tools and tests build subprocess environments with `render_env()`; never rely on the user's
shell profile (tools/AGENTS.md).
"""

from __future__ import annotations

import os
import platform
from pathlib import Path

TINYTEX_CANDIDATES = [
    Path.home() / "Library" / "TinyTeX" / "bin" / "universal-darwin",   # macOS (per-user)
    Path.home() / ".TinyTeX" / "bin" / "x86_64-linux",                  # Linux
    Path.home() / ".TinyTeX" / "bin" / "aarch64-linux",
]


def tinytex_bin() -> Path | None:
    for p in TINYTEX_CANDIDATES:
        if (p / "xelatex").exists():
            return p
    return None


def render_env(base: dict | None = None, **overrides) -> dict:
    """A copy of the environment with TeX on PATH and the given DSANIM_* overrides."""
    env = dict(os.environ if base is None else base)
    tex = tinytex_bin()
    if tex and str(tex) not in env.get("PATH", ""):
        env["PATH"] = f"{env.get('PATH', '')}:{tex}"
    env.update({k: str(v) for k, v in overrides.items()})
    return env


def describe() -> dict:
    return {"platform": platform.platform(), "tinytex": str(tinytex_bin()) if tinytex_bin() else None}
