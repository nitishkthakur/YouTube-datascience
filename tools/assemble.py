"""Join a tier's rendered scenes into one video, with YouTube chapters and SRT subtitles.

    uv run python tools/assemble.py <tier_dir> -q h [--vertical]

Reads renders/manifest_<q>[_v].json (from render_all.py) and script.md.
Writes  renders/<topic>_<tier>_<q>[_v].mp4
        publish/chapters[_v].txt      one line per scene: "M:SS Title" (paste into the description)
        publish/subtitles[_v].srt     caption cards timed from the beat sidecars (upload with the video)
        publish/manifest_<q>[_v].json what went in: scenes, beats, audio hashes, tool versions, git commit

Audio is normalised (AAC 48 kHz stereo; silence added to scenes without narration) so the
concat is a lossless stream copy of the video; a final pass then normalises loudness to
-14 LUFS (two-pass loudnorm) and tags BT.709 colour; -q h/-q k re-encode at crf 18.
Scene order = scene number in the file name.
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
sys.path.insert(0, str(Path(__file__).resolve().parent))   # sibling tools importable (render_all)


def has_audio(video: Path) -> bool:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                          "stream=codec_type", "-of", "csv=p=0", str(video)],
                         capture_output=True, text=True, check=True)
    return "audio" in out.stdout


def normalise(video: Path, dest: Path) -> Path:
    """Copy the video stream; decode (or synthesise) audio to PCM 48 kHz stereo in a .mov.

    PCM intermediates concatenate without AAC priming gaps at every seam; AAC is encoded once,
    in finalize()."""
    dest = dest.with_suffix(".mov")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if has_audio(video):
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(video),
               "-c:v", "copy", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", str(dest)]
    else:
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(video),
               "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
               "-c:v", "copy", "-c:a", "pcm_s16le", "-shortest", str(dest)]
    subprocess.run(cmd, check=True)
    return dest


def video_params(video: Path) -> str:
    """codec/profile/level/size/fps/pix_fmt — must match for a stream-copy concat to be valid."""
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                          "stream=codec_name,profile,level,width,height,r_frame_rate,pix_fmt",
                          "-of", "csv=p=0", str(video)], capture_output=True, text=True, check=True)
    return out.stdout.strip()


def check_provenance(tier: Path, scenes: list[dict], quality: str, vertical: bool) -> list[str]:
    """Renders whose inputs changed since they were made (scene file, common/, script, dsanim,
    audio). Assembling them would mix old and new."""
    from render_all import inputs_hash  # tools/ is on sys.path when run as a script

    stale = []
    for s in scenes:
        stamp = Path(s["mp4"]).with_suffix(".inputs.sha")
        entry = {"file": s["file"], "scene_number": s.get("scene_number"), "class": s["class"]}
        if not stamp.exists() or stamp.read_text().strip() != inputs_hash(entry, tier, quality, vertical):
            stale.append(s["class"])
    return stale


def concat(parts: list[Path], dest: Path) -> Path:
    params = {video_params(p) for p in parts}
    if len(params) > 1:
        raise SystemExit(f"cannot stream-copy concat: video parameters differ between scenes: {params} "
                         "— re-render the tier with one Manim/ffmpeg version")
    dest = dest.with_suffix(".mov")
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


LOUDNORM = "I=-14:TP=-1:LRA=11"   # YouTube / Instagram normalise to about -14 LUFS and only attenuate
BT709 = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]
BT709_BSF = "h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0"


def measure_loudness(video: Path) -> dict:
    """First loudnorm pass: measured integrated loudness, true peak, LRA, threshold."""
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(video), "-af", f"loudnorm={LOUDNORM}:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    text = r.stderr
    start = text.rfind("{")
    return json.loads(text[start:text.rfind("}") + 1]) if start >= 0 else {}


def finalize(src: Path, dest: Path, reencode: bool, crf: int = 18) -> dict:
    """Second loudnorm pass (linear, to the measured values) + BT.709 colour tags; finals
    re-encode the video at crf 18 so dark gradients survive the platform's re-encode."""
    if not has_audio(src):
        src = normalise(src, src.with_suffix(".silent.mp4"))   # platforms expect an audio track
    m = measure_loudness(src)
    silent = not m or float(m.get("input_i", "-inf")) < -60   # digital silence: nothing to normalise
    audio = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]
    if not silent:
        audio = ["-af", (f"loudnorm={LOUDNORM}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
                         f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
                         f"offset={m['target_offset']}:linear=true"), *audio]
    video = (["-c:v", "libx264", "-crf", str(crf), "-preset", "medium", "-pix_fmt", "yuv420p", *BT709]
             if reencode else ["-c:v", "copy", "-bsf:v", BT709_BSF])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), *video, *audio,
                    "-movflags", "+faststart", str(dest)], check=True)
    after = measure_loudness(dest) if not silent else {}

    def lufs(d):
        try:
            v = float(d["input_i"])
            return None if v == float("-inf") else v
        except (KeyError, ValueError, TypeError):
            return None

    return {"input_lufs": lufs(m), "output_lufs": lufs(after), "reencoded": reencode, "silent": silent}


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
                   offsets: list[float], output: Path, quality: str, vertical: bool,
                   seams: list[dict] | None = None, loudness: dict | None = None) -> Path:
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
        "seams": seams or [],
        "loudness": loudness or {},
        "video_params": video_params(output) if output.exists() else None,
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
    ap.add_argument("--allow-stale", action="store_true", help="assemble even if some renders predate their inputs")
    args = ap.parse_args(argv)

    tier = args.tier.resolve()
    tag = f"{args.quality}{'_v' if args.vertical else ''}"
    manifest = tier / "renders" / f"manifest_{tag}.json"
    if not manifest.exists():
        raise SystemExit(f"{manifest} missing — run tools/render_all.py first")
    scenes = json.loads(manifest.read_text())["scenes"]
    script = parse(tier / "script.md")
    stale = check_provenance(tier, scenes, args.quality, args.vertical)
    if stale and not args.allow_stale:
        raise SystemExit(f"stale renders (inputs changed since): {stale} — "
                         f"run tools/render_all.py {tier} -q {args.quality} first, or --allow-stale")

    work = tier / "renders" / ".concat"
    parts = [normalise(Path(s["mp4"]), work / f"{Path(s['mp4']).stem}.norm") for s in scenes]
    durations = [duration(p) for p in parts]
    offsets = [sum(durations[:i]) for i in range(len(durations))]

    name = f"{script.meta.get('topic', tier.parent.name)}_{script.meta.get('tier', tier.name)}_{tag}"
    joined = concat(parts, work / f"{name}.concat.mp4")
    out = tier / "renders" / f"{name}.mp4"
    loudness = finalize(joined, out, reencode=args.quality in "hk")
    fmt = lambda v: "silent" if v is None else f"{v:.1f} LUFS"
    print(f"loudness {fmt(loudness['input_lufs'])} -> {fmt(loudness['output_lufs'])}"
          f"{' (re-encoded crf 18, bt709)' if loudness['reencoded'] else ' (video copied, bt709 tagged)'}")

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
    write_manifest(publish / f"manifest_{tag}.json", script, scenes, parts, durations,
                   offsets, out, args.quality, args.vertical, seams=seams, loudness=loudness)

    total = sum(durations)
    print(f"assembled {out}  ({total:.1f}s, {len(scenes)} scenes)")
    print(f"chapters  {publish / f'chapters{suffix}.txt'}")
    print(f"subtitles {publish / f'subtitles{suffix}.srt'}  ({len(subs)} cards)")
    print(f"manifest  {publish / f'manifest_{tag}.json'}")
    return out


if __name__ == "__main__":
    main()
