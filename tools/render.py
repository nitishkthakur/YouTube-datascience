"""Render one scene and put the result where the review loop expects it.

    uv run python tools/render.py <scene_file.py> <SceneClass> [-q l|m|h|k] [--vertical]
                                  [--sheet] [--every 2]

- Output: <tier>/renders/<SceneClass>_<q>[_v].mp4 for topic scenes,
          gallery/renders/<SceneClass>_<q>[_v].mp4 for gallery scenes.
- --vertical sets DSANIM_VERTICAL=1 (9:16 frame; see dsanim/layout.py).
- -q h / -q k set DSANIM_FINAL=1: any PLACEHOLDER narration aborts the render.
- --sheet also writes the contact sheet (tools/contact_sheet.py) next to the video.
- Manim's partial-movie cache lives in media/ (git-ignored). Don't clear it unless corrupt.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TINYTEX = Path.home() / "Library" / "TinyTeX" / "bin" / "universal-darwin"


def renders_dir(scene_file: Path) -> Path:
    scene_file = scene_file.resolve()
    if scene_file.parent.name in ("scenes", "shorts"):
        return scene_file.parent.parent / "renders"
    return scene_file.parent / "renders"


def main(argv: list[str] | None = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("scene_file", type=Path)
    ap.add_argument("scene_class")
    ap.add_argument("-q", "--quality", default="l", choices=list("lmhk"))
    ap.add_argument("--vertical", action="store_true")
    ap.add_argument("--sheet", action="store_true", help="also build the contact sheet")
    ap.add_argument("--every", type=float, default=2.0, help="contact sheet interval (s)")
    args = ap.parse_args(argv)

    env = dict(os.environ)
    if TINYTEX.exists() and str(TINYTEX) not in env.get("PATH", ""):
        env["PATH"] = f"{env.get('PATH', '')}:{TINYTEX}"
    env["DSANIM_VERTICAL"] = "1" if args.vertical else "0"
    env["DSANIM_FINAL"] = "1" if args.quality in "hk" else "0"

    suffix = f"{args.scene_class}_{args.quality}{'_v' if args.vertical else ''}"
    media = ROOT / "media"
    cmd = [sys.executable, "-m", "manim", "render", f"-q{args.quality}",
           "--media_dir", str(media), "-o", suffix,
           str(args.scene_file), args.scene_class]
    print("+", " ".join(cmd), flush=True)
    t0 = time.time()
    subprocess.run(cmd, env=env, check=True, cwd=ROOT)
    elapsed = time.time() - t0

    produced = sorted(media.glob(f"videos/**/{suffix}.mp4"), key=lambda p: p.stat().st_mtime)
    if not produced:
        sys.exit(f"render finished but {suffix}.mp4 not found under {media}")
    out_dir = renders_dir(args.scene_file)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{suffix}.mp4"
    shutil.copy2(produced[-1], out)
    print(f"rendered {out}  ({elapsed:.1f}s wall)")

    if args.sheet:
        subprocess.run([sys.executable, str(ROOT / "tools" / "contact_sheet.py"), str(out),
                        "--every", str(args.every)], check=True)
    return out


if __name__ == "__main__":
    main()
