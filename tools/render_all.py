"""Render every scene of a tier (or a subset) at one quality, in script order.

    uv run python tools/render_all.py <tier_dir> -q l [--vertical] [--allow-placeholder]
                                     [--scenes s02_line.py ...] [--jobs 2] [--sheet]

Scene files are <tier>/scenes/sNN_<slug>.py, one DSScene subclass each; NN is the scene
number in script.md. A scene whose inputs (its file, common/, script.md, src/dsanim, the
tier's audio, quality, orientation) are unchanged since its last render is kept, not
re-rendered (--force overrides) — so a 10-minute topic re-renders only what changed. Each scene renders in its own process (tools/render.py) so Manim's
global config never leaks between scenes. Writes renders/manifest_<q>[_v].json — the ordered
list assemble.py and make_shorts.py consume.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dsanim import narration
from dsanim.script import parse

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


def _hash_tree(h, root: Path, suffixes=(".py", ".md", ".wav", ".json", ".csv")) -> None:
    if not root.exists():
        return
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix in suffixes and ".media" not in p.parts and "renders" not in p.parts:
            h.update(p.relative_to(root).as_posix().encode())
            h.update(hashlib.sha256(p.read_bytes()).digest())


def inputs_hash(entry: dict, tier: Path, quality: str, vertical: bool) -> str:
    """Everything a scene's render depends on: its file, the tier's common/ and script, the
    dsanim library, the tier's audio (recorded + placeholder), quality and orientation."""
    import manim

    h = hashlib.sha256()
    h.update(Path(entry["file"]).read_bytes())
    _hash_tree(h, tier / "common")
    h.update((tier / "script.md").read_bytes() if (tier / "script.md").exists() else b"")
    _hash_tree(h, ROOT / "src" / "dsanim")
    try:
        _hash_tree(h, narration.beat_dir(parse(tier / "script.md")))
    except (ValueError, FileNotFoundError):
        pass
    h.update(f"{quality}|{vertical}|{manim.__version__}".encode())
    return h.hexdigest()


def manifest_path(tier: Path, quality: str, vertical: bool) -> Path:
    return tier / "renders" / f"manifest_{quality}{'_v' if vertical else ''}.json"


def probe_duration(video: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                          "default=nw=1:nk=1", str(video)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def render_one(entry: dict, quality: str, vertical: bool, allow_placeholder: bool,
               sheet: bool, force: bool = False) -> dict:
    tier = Path(entry["file"]).parent.parent
    tag = f"{entry['class']}_{quality}{'_v' if vertical else ''}"
    out = tier / "renders" / f"{tag}.mp4"
    beats = out.with_suffix(".beats.json")
    stamp = out.with_suffix(".inputs.sha")
    digest = inputs_hash(entry, tier, quality, vertical)
    if not force and out.exists() and beats.exists() and stamp.exists() and stamp.read_text().strip() == digest:
        return {**entry, "mp4": str(out), "beats_json": str(beats), "duration": probe_duration(out),
                "log": "", "skipped": True}
    cmd = [sys.executable, str(ROOT / "tools" / "render.py"), entry["file"], entry["class"],
           "-q", quality]
    if vertical:
        cmd.append("--vertical")
    if allow_placeholder:
        cmd.append("--allow-placeholder")
    if sheet:
        cmd.append("--sheet")
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    log = out.with_suffix(".log")
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(r.stdout + "\n" + r.stderr)     # the full Manim output, for a run nobody watched
    if r.returncode != 0 or not out.exists():
        raise RuntimeError(f"{entry['class']} failed (log: {log}):\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    stamp.write_text(digest)
    return {**entry, "mp4": str(out), "beats_json": str(beats) if beats.exists() else None,
            "duration": probe_duration(out), "log": r.stdout[-400:], "skipped": False}


def main(argv: list[str] | None = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("tier", type=Path)
    ap.add_argument("-q", "--quality", default="l", choices=list("lmhk"))
    ap.add_argument("--vertical", action="store_true")
    ap.add_argument("--allow-placeholder", action="store_true")
    ap.add_argument("--scenes", nargs="*", help="only these scene files (basenames)")
    ap.add_argument("--jobs", type=int, default=1, help="scenes rendered in parallel")
    ap.add_argument("--sheet", action="store_true", help="also build contact sheets")
    ap.add_argument("--force", action="store_true", help="re-render even if inputs are unchanged")
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
            lambda e: render_one(e, args.quality, args.vertical, args.allow_placeholder, args.sheet, args.force),
            entries))
    for r in results:
        print(f"  {r['class']:<12} {r['duration']:6.1f}s  {'(unchanged, kept)' if r.get('skipped') else ''}  {r['mp4']}")

    path = manifest_path(tier, args.quality, args.vertical)
    path.parent.mkdir(parents=True, exist_ok=True)
    if args.scenes and path.exists():
        # a subset render updates its entries in the existing manifest instead of replacing it;
        # entries whose scene file no longer exists are dropped
        previous = {s["file"]: s for s in json.loads(path.read_text()).get("scenes", [])
                    if Path(s.get("file", "")).exists()}
        previous.update({r["file"]: r for r in results})
        results = sorted(previous.values(), key=lambda s: s.get("scene_number", 0))
    path.write_text(json.dumps({"tier": str(tier), "quality": args.quality,
                                "vertical": args.vertical, "scenes": results}, indent=1))
    print(f"manifest {path}")
    return path


if __name__ == "__main__":
    main()
