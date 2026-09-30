"""Validate a script.md and report what each beat needs.

    uv run python tools/check_script.py <tier_dir or script.md> [--scenes]

Prints every beat with its word count, estimated duration, audio status (recorded /
placeholder / missing), marks and equations. With --scenes, also checks that every
self.eq("<id>") / self.beat("<id>") referenced from scenes/ exists in the script, and
lists beats that no scene plays yet. Exit 1 on any problem.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from dsanim import narration
from dsanim.script import ScriptError, parse

EQ_REF = re.compile(r"self\.eq\(\s*[\"']([A-Za-z0-9_\-]+)[\"']")
BEAT_REF = re.compile(r"self\.beat\(\s*[\"'](\d+\.\d+)[\"']")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("target", type=Path)
    ap.add_argument("--scenes", action="store_true")
    args = ap.parse_args()
    path = args.target / "script.md" if args.target.is_dir() else args.target

    try:
        script = parse(path)
    except ScriptError as e:
        print(f"ERROR {e}")
        return 1

    problems = 0
    print(f"{path}  status={script.meta.get('status', 'draft')}  "
          f"topic={script.meta.get('topic')}  tier={script.meta.get('tier')}")
    total = 0.0
    for n, sc in script.scenes.items():
        print(f"\nScene {n} — {sc.title}")
        for bid in sc.beats:
            b = script.beats[bid]
            try:
                a = narration.load(script, b)
                status, dur = a.kind, a.duration
            except ValueError as e:
                print(f"ERROR {e}")
                return 1
            total += dur
            marks = ",".join(m.name for m in b.marks) or "-"
            eqs = ",".join(b.equations) or "-"
            print(f"  {bid:>5} {b.key}  {len(b.words):3d} words  {dur:5.1f}s {status:15s}"
                  f" marks[{marks}] eqs[{eqs}]")
            if not b.words:
                print(f"  ERROR beat {bid} has no narration")
                problems += 1
    print(f"\nTotal narration ≈ {total / 60:.1f} min")

    if args.scenes:
        scene_dir = path.parent / "scenes"
        used_beats: set[str] = set()
        for f in sorted(scene_dir.glob("*.py")):
            src = f.read_text()
            for eid in EQ_REF.findall(src):
                if eid not in script.equations:
                    print(f"ERROR {f.name}: self.eq({eid!r}) not in script.md")
                    problems += 1
            for bid in BEAT_REF.findall(src):
                used_beats.add(bid)
                if bid not in script.beats:
                    print(f"ERROR {f.name}: self.beat({bid!r}) not in script.md")
                    problems += 1
        missing = [b for b in script.beats if b not in used_beats]
        if missing:
            print(f"beats not yet played by any scene: {', '.join(missing)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
