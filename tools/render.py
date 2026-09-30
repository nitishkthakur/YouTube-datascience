"""Render one scene and put the result where the review loop expects it.

    uv run python tools/render.py <scene_file.py> <SceneClass> [-q l|m|h|k] [--vertical]
                                  [--sheet] [--every 2]

- Output: <tier>/renders/<SceneClass>_<q>[_v].mp4 for topic scenes,
          gallery/renders/<SceneClass>_<q>[_v].mp4 for gallery scenes.
- --vertical sets DSANIM_VERTICAL=1 (9:16 frame; see dsanim/layout.py).
- -q h / -q k set DSANIM_FINAL=1: the script must be frozen and any PLACEHOLDER narration
  aborts the render — unless --allow-placeholder, which makes a *test render*: unfrozen
  scripts allowed, placeholder voice allowed but watermarked "PLACEHOLDER VOICE".
- The beat timings sidecar written by DSScene is copied next to the video as
  <name>.beats.json (used by assemble.py and make_shorts.py).
- --sheet also writes the contact sheet (tools/contact_sheet.py) next to the video.
- Manim's media (partial-movie cache, TeX) lives in <renders>/.media/ per tier or gallery,
  so identical class names in different tiers never collide. Git-ignored with renders/.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from dsanim.env import render_env

ROOT = Path(__file__).resolve().parents[1]


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
    ap.add_argument("--allow-placeholder", action="store_true",
                    help="test render: allow placeholder audio (watermarked) and unfrozen scripts at -q h/k")
    ap.add_argument("--sheet", action="store_true", help="also build the contact sheet")
    ap.add_argument("--every", type=float, default=2.0, help="contact sheet interval (s)")
    args = ap.parse_args(argv)

    env = render_env(
        DSANIM_VERTICAL=int(args.vertical),
        DSANIM_FINAL=int(args.quality in "hk"),
        DSANIM_ALLOW_PLACEHOLDER=int(args.allow_placeholder),
    )

    suffix = f"{args.scene_class}_{args.quality}{'_v' if args.vertical else ''}"
    out_dir = renders_dir(args.scene_file)
    media = out_dir / ".media"
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
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{suffix}.mp4"
    shutil.copy2(produced[-1], out)
    timings = media / "timings" / f"{suffix}.json"
    if timings.exists():
        shutil.copy2(timings, out.with_suffix(".beats.json"))
    print(f"rendered {out}  ({elapsed:.1f}s wall)")

    if args.sheet:
        subprocess.run([sys.executable, str(ROOT / "tools" / "contact_sheet.py"), str(out),
                        "--every", str(args.every)], check=True)
    return out


if __name__ == "__main__":
    main()
