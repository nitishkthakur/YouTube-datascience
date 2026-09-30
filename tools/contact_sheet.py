"""Frames every N seconds -> one PNG grid, for agents (who cannot watch video) to inspect.

    uv run python tools/contact_sheet.py <video.mp4> [--every 2] [--cols 4] [--no-safe]
                                        [--start 8 --end 14]   # dense strip of one beat

Writes <video>.sheet.png next to the video. Each tile is labelled with its timestamp and
carries a thin outline of the 5% safe-area margin, so anything crossing it is obvious.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

TILE_W = 640
LABEL_H = 28
SAFE = 0.05
SAFE_COLOUR = (248, 113, 113)  # review overlay only — not part of the video palette


def duration(video: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "json", str(video)], capture_output=True, text=True, check=True)
    return float(json.loads(out.stdout)["format"]["duration"])


def grab(video: Path, t: float | None, dest: Path) -> None:
    """Frame at time t; t=None means the very last frame (seeking near the end can miss it)."""
    seek = ["-sseof", "-0.5"] if t is None else ["-ss", f"{t:.3f}"]
    extra = ["-update", "1"] if t is None else ["-frames:v", "1"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *seek, "-i", str(video), *extra, str(dest)],
                   check=True)
    if not dest.exists():
        raise RuntimeError(f"ffmpeg produced no frame at t={t} from {video}")


def main() -> Path:
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=Path)
    ap.add_argument("--every", type=float, default=2.0)
    ap.add_argument("--start", type=float, default=0.0, help="first sampled second")
    ap.add_argument("--end", type=float, default=None, help="last sampled second (default: video end)")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--no-safe", action="store_true")
    args = ap.parse_args()

    total = duration(args.video)
    end = total if args.end is None else min(args.end, total)
    times: list[float | None] = [t for t in _frange(args.start, end, args.every) if end - t > 0.25]
    if args.end is None:
        times.append(None)  # always include the final frame (the end state)
    else:
        times.append(end)

    try:
        font = ImageFont.truetype("Menlo.ttc", 18)
    except OSError:
        font = ImageFont.load_default()

    tiles = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, t in enumerate(times):
            p = Path(tmp) / f"{i:04d}.png"
            grab(args.video, t, p)
            im = Image.open(p).convert("RGB")
            scale = TILE_W / im.width
            im = im.resize((TILE_W, round(im.height * scale)))
            tile = Image.new("RGB", (im.width, im.height + LABEL_H), (0, 0, 0))
            tile.paste(im, (0, LABEL_H))
            d = ImageDraw.Draw(tile)
            stamp = f"t={t:6.2f}s" if t is not None else f"t={total:6.2f}s (end)"
            d.text((8, 4), stamp, fill=(230, 230, 230), font=font)
            if not args.no_safe:
                mx, my = SAFE * im.width, SAFE * im.height
                d.rectangle([mx, LABEL_H + my, im.width - mx, LABEL_H + im.height - my],
                            outline=SAFE_COLOUR, width=1)
            tiles.append(tile)

    cols = min(args.cols, len(tiles))
    rows = -(-len(tiles) // cols)
    tw, th = tiles[0].size
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * 6, rows * th + (rows + 1) * 6), (40, 40, 40))
    for i, tile in enumerate(tiles):
        r, c = divmod(i, cols)
        sheet.paste(tile, (6 + c * (tw + 6), 6 + r * (th + 6)))
    out = args.video.with_suffix(".sheet.png")
    sheet.save(out)
    print(f"contact sheet {out}  ({len(tiles)} frames, {total:.1f}s video)")
    return out


def _frange(a: float, b: float, step: float):
    t = a
    while t < b:
        yield t
        t += step


if __name__ == "__main__":
    main()
