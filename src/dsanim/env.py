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


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_dotenv(path: Path | None = None) -> dict[str, str]:
    """Read KEY=VALUE lines from <repo>/.env into os.environ (existing values win)."""
    path = path or repo_root() / ".env"
    loaded = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v
                loaded[k] = v
    return loaded


def tinytex_bin() -> Path | None:
    for p in TINYTEX_CANDIDATES:
        if (p / "xelatex").exists():
            return p
    return None


def render_env(base: dict | None = None, **overrides) -> dict:
    """A copy of the environment with TeX on PATH and the given DSANIM_* overrides."""
    load_dotenv()
    env = dict(os.environ if base is None else base)
    tex = tinytex_bin()
    if tex and str(tex) not in env.get("PATH", ""):
        env["PATH"] = f"{env.get('PATH', '')}:{tex}"
    env.update({k: str(v) for k, v in overrides.items()})
    return env


def scene_env(scene_file: Path, **overrides) -> dict:
    """render_env() plus the scene's tier and concept folders on PYTHONPATH (for `common/`)."""
    env = render_env(**overrides)
    tier = Path(scene_file).resolve().parent.parent
    extra = f"{tier}:{tier.parent}"
    env["PYTHONPATH"] = f"{extra}:{env['PYTHONPATH']}" if env.get("PYTHONPATH") else extra
    return env


def describe() -> dict:
    return {"platform": platform.platform(), "tinytex": str(tinytex_bin()) if tinytex_bin() else None}
