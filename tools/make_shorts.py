"""Cut vertical chunks (Shorts / Reels) from a tier, as declared in shorts/chunks.yaml.

    uv run python tools/make_shorts.py <tier_dir> [-q h] [--allow-placeholder] [--jobs 2]

shorts/chunks.yaml:
    chunks:
      - name: the-line-is-a-mean          # output file name
        scenes: [s02_line.py, s03_band.py] # rendered vertically, in this order
        from_beat: "2.2"                   # optional: start at this beat of the first scene
        to_beat: "3.1"                     # optional: end after this beat of the last scene

A chunk is one or more whole scenes, optionally trimmed to a beat range using the beat
timings sidecars. Vertical renders (captions burned in) are made if missing. Trimmed pieces
are re-encoded (frame-accurate cuts); output: renders/shorts/<name>_<q>.mp4.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ENCODE = ["-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
          "-c:a", "aac", "-ar", "48000", "-ac", "2"]


def load_chunks(tier: Path) -> list[dict]:
    path = tier / "shorts" / "chunks.yaml"
    if not path.exists():
        return []
    spec = yaml.safe_load(path.read_text()) or {}
    chunks = spec.get("chunks") or []
    for c in chunks:
        if "name" not in c or not c.get("scenes"):
            raise SystemExit(f"{path}: every chunk needs 'name' and a non-empty 'scenes' list")
    return chunks


def beat_window(beats_json: Path, from_beat: str | None, to_beat: str | None
                ) -> tuple[float | None, float | None]:
    """(start, end) seconds within the scene, or None for 'from the start' / 'to the end'."""
    beats = {b["id"]: b for b in json.loads(beats_json.read_text())["beats"]}
    for wanted in (from_beat, to_beat):
        if wanted and wanted not in beats:
            raise KeyError(f"{beats_json}: no beat {wanted}; has {list(beats)}")
    start = beats[from_beat]["start"] if from_beat else None
    end = beats[to_beat]["end"] if to_beat else None
    return start, end


def cut(video: Path, dest: Path, start: float | None, end: float | None) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-v", "error", "-y"]
    if start is not None:
        cmd += ["-ss", f"{start:.3f}"]
    if end is not None:
        cmd += ["-to", f"{end:.3f}"]
    cmd += ["-i", str(video), *ENCODE, str(dest)]
    subprocess.run(cmd, check=True)
    return dest


def concat(parts: list[Path], dest: Path) -> Path:
    listing = dest.with_suffix(".concat.txt")
    listing.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
                    "-i", str(listing), "-c", "copy", str(dest)], check=True)
    listing.unlink()
    return dest


def ensure_vertical_renders(tier: Path, files: list[str], quality: str, allow_placeholder: bool,
                            jobs: int) -> dict[str, dict]:
    """Render the listed scene files vertically if their mp4 (+ sidecar) is missing."""
    from render_all import discover  # tools/ is on sys.path when run as a script

    entries = {Path(e["file"]).name: e for e in discover(tier)}
    missing = [f for f in files if f not in entries]
    if missing:
        raise SystemExit(f"unknown scene files in chunks.yaml: {missing}")
    todo = []
    for f in files:
        e = entries[f]
        mp4 = tier / "renders" / f"{e['class']}_{quality}_v.mp4"
        if not mp4.exists() or not mp4.with_suffix(".beats.json").exists():
            todo.append(f)
    if todo:
        cmd = [sys.executable, str(ROOT / "tools" / "render_all.py"), str(tier), "-q", quality,
               "--vertical", "--scenes", *todo, "--jobs", str(jobs)]
        if allow_placeholder:
            cmd.append("--allow-placeholder")
        subprocess.run(cmd, check=True, cwd=ROOT)
    return entries


def main(argv: list[str] | None = None) -> list[Path]:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("tier", type=Path)
    ap.add_argument("-q", "--quality", default="h", choices=list("lmhk"))
    ap.add_argument("--allow-placeholder", action="store_true")
    ap.add_argument("--jobs", type=int, default=1)
    args = ap.parse_args(argv)

    tier = args.tier.resolve()
    chunks = load_chunks(tier)
    if not chunks:
        print(f"no chunks declared in {tier / 'shorts' / 'chunks.yaml'}")
        return []
    files = sorted({f for c in chunks for f in c["scenes"]})
    entries = ensure_vertical_renders(tier, files, args.quality, args.allow_placeholder, args.jobs)

    outputs = []
    for c in chunks:
        work = tier / "renders" / "shorts" / ".work" / c["name"]
        parts = []
        for i, f in enumerate(c["scenes"]):
            e = entries[f]
            video = tier / "renders" / f"{e['class']}_{args.quality}_v.mp4"
            start, end = beat_window(
                video.with_suffix(".beats.json"),
                c.get("from_beat") if i == 0 else None,
                c.get("to_beat") if i == len(c["scenes"]) - 1 else None)
            parts.append(cut(video, work / f"{i:02d}_{e['class']}.mp4", start, end))
        out = concat(parts, tier / "renders" / "shorts" / f"{c['name']}_{args.quality}.mp4")
        print(f"short {out}")
        outputs.append(out)
    return outputs


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
