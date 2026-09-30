"""The deterministic pipeline: one command from a tier folder to finished files.

    uv run python tools/pipeline.py <tier_dir> [--qualities l m h] [--allow-placeholder]
                                   [--jobs 2] [--skip-shorts] [--sheet]

Steps (each is its own tool, runnable alone):
  1. status.py            what is present / missing and who supplies it
  2. tts_placeholder.py   only with --allow-placeholder: Kokoro audio for beats with no recording
  3. render_all.py        every scene at each quality (16:9), contact sheets with --sheet
  4. assemble.py          one video per quality + publish/chapters.txt + publish/subtitles.srt
  5. make_shorts.py       vertical chunks from shorts/chunks.yaml at the highest quality asked
  6. status.py            again, so the last thing printed is what is still missing

Stops at the first failure. Without --allow-placeholder a beat with no recording fails the
-q h step (AGENTS.md §7): that is the guard against publishing a placeholder voice.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"


def run(step: str, cmd: list[str]) -> None:
    print(f"\n=== {step}: {' '.join(str(c) for c in cmd[1:])}", flush=True)
    t0 = time.time()
    r = subprocess.run([sys.executable, *cmd], cwd=ROOT)
    if r.returncode != 0:
        raise SystemExit(f"pipeline stopped: {step} failed (exit {r.returncode})")
    print(f"=== {step} done in {time.time() - t0:.0f}s", flush=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("tier", type=Path)
    ap.add_argument("--qualities", nargs="+", default=["l", "m", "h"], choices=list("lmhk"))
    ap.add_argument("--allow-placeholder", action="store_true",
                    help="generate placeholder narration where missing and allow it in -q h/-q k (watermarked)")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--skip-shorts", action="store_true")
    ap.add_argument("--sheet", action="store_true", help="contact sheets for the 720p renders")
    args = ap.parse_args(argv)
    tier = str(args.tier.resolve())
    allow = ["--allow-placeholder"] if args.allow_placeholder else []

    run("status", [TOOLS / "status.py", tier])
    if args.allow_placeholder:
        run("placeholder narration", [TOOLS / "tts_placeholder.py", tier])
    for q in args.qualities:
        sheet = ["--sheet"] if (args.sheet and q == "m") else []
        run(f"render -q {q}", [TOOLS / "render_all.py", tier, "-q", q, "--jobs", str(args.jobs), *allow, *sheet])
        run(f"assemble -q {q}", [TOOLS / "assemble.py", tier, "-q", q])
    if not args.skip_shorts:
        best = max(args.qualities, key="lmhk".index)
        run("shorts", [TOOLS / "make_shorts.py", tier, "-q", best, "--jobs", str(args.jobs), *allow])
    run("status", [TOOLS / "status.py", tier])
    return 0


if __name__ == "__main__":
    sys.exit(main())
