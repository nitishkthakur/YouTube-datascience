"""Scaffold a concept folder and/or a tier inside it from topics/_template.

    uv run python tools/new_topic.py 030-regression-is-conditional-distribution L1

Creates topics/<concept>/ (README.md) if missing, then topics/<concept>/<tier>/ with
script.md, shotlist.md, NOTES.md, scenes/, shorts/, publish/. Never overwrites.
Remember to add the concept to channel/curriculum.md.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONCEPT_RE = re.compile(r"^\d{3}-[a-z0-9]+(?:-[a-z0-9]+)*$")
TIERS = ("L1", "L2", "L3")


def main(argv: list[str] | None = None, root: Path = ROOT) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print(__doc__)
        return 1
    concept, tier = argv
    template = root / "topics" / "_template"
    if not CONCEPT_RE.match(concept):
        sys.exit(f"concept must look like 030-some-slug, got {concept!r}")
    if tier not in TIERS:
        sys.exit(f"tier must be one of {TIERS}")

    cdir = root / "topics" / concept
    if not cdir.exists():
        cdir.mkdir(parents=True)
        readme = (template / "README.md").read_text().replace("{{concept}}", concept)
        (cdir / "README.md").write_text(readme)
        print(f"created {cdir.relative_to(root)}/README.md")

    tdir = cdir / tier
    if tdir.exists():
        sys.exit(f"{tdir.relative_to(root)} already exists")
    shutil.copytree(template / "TIER", tdir)
    for f in tdir.rglob("*.md"):
        f.write_text(f.read_text().replace("{{concept}}", concept).replace("{{tier}}", tier))
    print(f"created {tdir.relative_to(root)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
