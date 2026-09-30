"""Render every scene of a tier (or a subset) at one quality, in script order.

    uv run python tools/render_all.py <tier_dir> -q l [--vertical] [--allow-placeholder]
                                     [--scenes s02_line.py ...] [--jobs 2] [--sheet]

Scene files are <tier>/scenes/sNN_<slug>.py, one DSScene subclass each; NN is the scene
number in script.md. Each scene renders in its own process (tools/render.py) so Manim's
global config never leaks between scenes. Writes renders/manifest_<q>[_v].json — the ordered
list assemble.py and make_shorts.py consume.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENE_FILE_RE = re.compile(r"^s(\d{2})_[a-z0-9_]+\.py$")
CLASS_RE = re.compile(r"^class\s+(\w+)\s*\(\s*DSScene\s*\)", re.M)


def discover(tier: Path) -> list[dict]:
    """[{file, scene_number, class}] for every sNN_*.py under <tier>/scenes, sorted."""
    out = []
    for f in sorted((tier / "scenes").glob("*.py")):
        m = SCENE_FILE_RE.match(f.name)
        if not m:
            continue
        classes = CLASS_RE.findall(f.read_text())
        if len(classes) != 1:
            raise SystemExit(f"{f}: expected exactly one `class X(DSScene)`, found {classes}")
        out.append({"file": str(f), "scene_number": int(m.group(1)), "class": classes[0]})
    return out


def manifest_path(tier: Path, quality: str, vertical: bool) -> Path:
    return tier / "renders" / f"manifest_{quality}{'_v' if vertical else ''}.json"


def probe_duration(video: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                          "default=nw=1:nk=1", str(video)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def render_one(entry: dict, quality: str, vertical: bool, allow_placeholder: bool,
               sheet: bool) -> dict:
    cmd = [sys.executable, str(ROOT / "tools" / "render.py"), entry["file"], entry["class"],
           "-q", quality]
    if vertical:
        cmd.append("--vertical")
    if allow_placeholder:
        cmd.append("--allow-placeholder")
    if sheet:
        cmd.append("--sheet")
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    tag = f"{entry['class']}_{quality}{'_v' if vertical else ''}"
    out = Path(entry["file"]).parent.parent / "renders" / f"{tag}.mp4"
    if r.returncode != 0 or not out.exists():
        raise RuntimeError(f"{entry['class']} failed:\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}")
    beats = out.with_suffix(".beats.json")
    return {**entry, "mp4": str(out), "beats_json": str(beats) if beats.exists() else None,
            "duration": probe_duration(out), "log": r.stdout[-400:]}


def main(argv: list[str] | None = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("tier", type=Path)
    ap.add_argument("-q", "--quality", default="l", choices=list("lmhk"))
    ap.add_argument("--vertical", action="store_true")
    ap.add_argument("--allow-placeholder", action="store_true")
    ap.add_argument("--scenes", nargs="*", help="only these scene files (basenames)")
    ap.add_argument("--jobs", type=int, default=1, help="scenes rendered in parallel")
    ap.add_argument("--sheet", action="store_true", help="also build contact sheets")
    args = ap.parse_args(argv)

    tier = args.tier.resolve()
    entries = discover(tier)
    if args.scenes:
        wanted = set(args.scenes)
        entries = [e for e in entries if Path(e["file"]).name in wanted]
        missing = wanted - {Path(e["file"]).name for e in entries}
        if missing:
            raise SystemExit(f"unknown scene files: {sorted(missing)}")
    if not entries:
        raise SystemExit(f"no sNN_*.py scenes under {tier / 'scenes'}")

    print(f"rendering {len(entries)} scene(s) at -q{args.quality}"
          f"{' vertical' if args.vertical else ''}, jobs={args.jobs}", flush=True)
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        results = list(pool.map(
            lambda e: render_one(e, args.quality, args.vertical, args.allow_placeholder, args.sheet),
            entries))
    for r in results:
        print(f"  {r['class']:<12} {r['duration']:6.1f}s  {r['mp4']}")

    path = manifest_path(tier, args.quality, args.vertical)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"tier": str(tier), "quality": args.quality,
                                "vertical": args.vertical, "scenes": results}, indent=1))
    print(f"manifest {path}")
    return path


if __name__ == "__main__":
    main()
