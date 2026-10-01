"""Join a tier's rendered scenes into one video, with YouTube chapters and SRT subtitles.

    uv run python tools/assemble.py <tier_dir> -q h [--vertical]

Reads renders/manifest_<q>[_v].json (from render_all.py) and script.md.
Writes  renders/<topic>_<tier>_<q>[_v].mp4
        publish/chapters[_v].txt      one line per scene: "M:SS Title" (paste into the description)
        publish/subtitles[_v].srt     caption cards timed from the beat sidecars (upload with the video)
        publish/manifest_<q>[_v].json what went in: scenes, beats, audio hashes, tool versions, git commit

Audio is normalised (AAC 48 kHz stereo; silence added to scenes without narration) so the
concat is a lossless stream copy of the video. Scene order = scene number in the file name.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from dsanim import captions
from dsanim.script import parse

ROOT = Path(__file__).resolve().parents[1]


def has_audio(video: Path) -> bool:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                          "stream=codec_type", "-of", "csv=p=0", str(video)],
                         capture_output=True, text=True, check=True)
    return "audio" in out.stdout


def normalise(video: Path, dest: Path) -> Path:
    """Copy the video stream; transcode (or synthesise) audio to AAC 48 kHz stereo."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if has_audio(video):
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(video),
               "-c:v", "copy", "-c:a", "aac", "-ar", "48000", "-ac", "2", str(dest)]
    else:
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(video),
               "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
               "-c:v", "copy", "-c:a", "aac", "-shortest", str(dest)]
    subprocess.run(cmd, check=True)
    return dest


def concat(parts: list[Path], dest: Path) -> Path:
    listing = dest.with_suffix(".concat.txt")
    listing.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
                    "-i", str(listing), "-c", "copy", str(dest)], check=True)
    listing.unlink()
    return dest


def duration(video: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                          "default=nw=1:nk=1", str(video)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def frame_at(video: Path, dest: Path, last: bool) -> Path:
    seek = ["-sseof", "-0.2"] if last else ["-ss", "0"]
    extra = ["-update", "1"] if last else ["-frames:v", "1"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *seek, "-i", str(video), *extra, str(dest)], check=True)
    return dest


def seam_report(parts: list[Path], work: Path, threshold: float = 0.02) -> list[dict]:
    """How much changes across each cut: fraction of pixels that differ between the last frame
    of scene N and the first frame of scene N+1. A hard cut in a continuous layout shows up as
    a large fraction; report it so the shot list's TRANSITION can be checked."""
    import numpy as np
    from PIL import Image

    out = []
    for a, b in zip(parts, parts[1:]):
        fa = frame_at(a, work / f"{a.stem}.last.png", last=True)
        fb = frame_at(b, work / f"{b.stem}.first.png", last=False)
        ia = np.asarray(Image.open(fa).convert("RGB"), dtype=float)
        ib = np.asarray(Image.open(fb).convert("RGB"), dtype=float)
        changed = float((np.abs(ia - ib).max(axis=-1) > 24).mean()) if ia.shape == ib.shape else 1.0
        out.append({"from": a.stem.replace(".norm", ""), "to": b.stem.replace(".norm", ""),
                    "changed_fraction": round(changed, 4), "hard_cut": changed > threshold})
    return out


def chapter_stamp(t: float) -> str:
    t = int(round(t))
    h, rest = divmod(t, 3600)
    m, s = divmod(rest, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def chapters_and_subtitles(script, scenes: list[dict], offsets: list[float]
                           ) -> tuple[list[str], list[tuple[float, float, str]]]:
    chapters, subs = [], []
    for entry, offset in zip(scenes, offsets):
        title = script.scenes[entry["scene_number"]].title if entry["scene_number"] in script.scenes \
            else entry["class"]
        chapters.append(f"{chapter_stamp(offset)} {title}")
        if entry.get("beats_json") and Path(entry["beats_json"]).exists():
            sidecar = json.loads(Path(entry["beats_json"]).read_text())
            for beat in sidecar["beats"]:
                for c in beat["captions"]:
                    subs.append((offset + beat["start"] + c["start"],
                                 offset + beat["start"] + c["end"], c["text"]))
    return chapters, subs


def environment() -> dict:
    """What produced this render — enough to reproduce or to explain a difference later."""
    import manim
    ffmpeg = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout.split("\n")[0]
    git = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=ROOT).stdout.strip() != ""
    return {"python": sys.version.split()[0], "manim": manim.__version__, "ffmpeg": ffmpeg,
            "platform": platform.platform(), "git_commit": git, "git_dirty": dirty,
            "rendered_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def write_manifest(path: Path, script, scenes: list[dict], parts: list[Path], durations: list[float],
                   offsets: list[float], output: Path, quality: str, vertical: bool) -> Path:
    beats = []
    for entry, offset in zip(scenes, offsets):
        if entry.get("beats_json") and Path(entry["beats_json"]).exists():
            side = json.loads(Path(entry["beats_json"]).read_text())
            for b in side["beats"]:
                beats.append({"scene": entry["class"], "id": b["id"], "key": b["key"],
                              "start": offset + b["start"], "end": offset + b["end"],
                              "audio": b["audio"], "audio_file": b.get("audio_file"),
                              "audio_sha256": b.get("audio_sha256")})
    manifest = {
        "topic": script.meta.get("topic"), "tier": script.meta.get("tier"),
        "script_status": script.meta.get("status", "draft"), "quality": quality, "vertical": vertical,
        "output": str(output), "duration": sum(durations),
        "scenes": [{"class": e["class"], "file": e["file"], "duration": d, "offset": o}
                   for e, d, o in zip(scenes, durations, offsets)],
        "beats": beats,
        "placeholder_audio": any(b["audio"] == "placeholder" for b in beats),
        "environment": environment(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=1))
    return path


def main(argv: list[str] | None = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("tier", type=Path)
    ap.add_argument("-q", "--quality", default="h", choices=list("lmhk"))
    ap.add_argument("--vertical", action="store_true")
    args = ap.parse_args(argv)

    tier = args.tier.resolve()
    tag = f"{args.quality}{'_v' if args.vertical else ''}"
    manifest = tier / "renders" / f"manifest_{tag}.json"
    if not manifest.exists():
        raise SystemExit(f"{manifest} missing — run tools/render_all.py first")
    scenes = json.loads(manifest.read_text())["scenes"]
    script = parse(tier / "script.md")

    work = tier / "renders" / ".concat"
    parts = [normalise(Path(s["mp4"]), work / f"{Path(s['mp4']).stem}.norm.mp4") for s in scenes]
    durations = [duration(p) for p in parts]
    offsets = [sum(durations[:i]) for i in range(len(durations))]

    name = f"{script.meta.get('topic', tier.parent.name)}_{script.meta.get('tier', tier.name)}_{tag}"
    out = concat(parts, tier / "renders" / f"{name}.mp4")

    seams = seam_report(parts, work)
    for s in seams:
        flag = "HARD CUT" if s["hard_cut"] else "continuous"
        print(f"seam {s['from']} -> {s['to']}: {s['changed_fraction']:.1%} of pixels change ({flag})")
    chapters, subs = chapters_and_subtitles(script, scenes, offsets)
    publish = tier / "publish"
    publish.mkdir(exist_ok=True)
    suffix = "_v" if args.vertical else ""
    (publish / f"chapters{suffix}.txt").write_text("\n".join(chapters) + "\n")
    captions.write_srt(subs, publish / f"subtitles{suffix}.srt")
    manifest = write_manifest(publish / f"manifest_{tag}.json", script, scenes, parts, durations,
                              offsets, out, args.quality, args.vertical)
    data = json.loads(manifest.read_text())
    data["seams"] = seams
    manifest.write_text(json.dumps(data, indent=1))

    total = sum(durations)
    print(f"assembled {out}  ({total:.1f}s, {len(scenes)} scenes)")
    print(f"chapters  {publish / f'chapters{suffix}.txt'}")
    print(f"subtitles {publish / f'subtitles{suffix}.srt'}  ({len(subs)} cards)")
    print(f"manifest  {publish / f'manifest_{tag}.json'}")
    return out


if __name__ == "__main__":
    main()
