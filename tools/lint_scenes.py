"""Mechanical enforcement of AGENTS.md rules that agents most often break.

    uv run python tools/lint_scenes.py [files...]     # no args: lint the whole repo
    uv run python tools/lint_scenes.py --hook         # Claude Code hook: tool-call JSON on stdin

Exit 0 = clean (warnings may print), exit 2 = violations (the hook feeds them back to Claude).

Rules
  everywhere (src/, gallery/, topics/):
    E1  ManimGL-isms: manimlib, ShowCreation, TextMobject, TexMobject, CONFIG dicts
    E2  hex colour literals outside src/dsanim/palette.py
  topic scenes (topics/**.py):
    E3  MathTex/Tex built from a string literal — use self.eq("<id>") from script.md
    E4  Manim built-in colour constants (BLUE, RED, ...) — use dsanim.palette as P
    W1  self.wait(<number>) — beat timing should come from narration (self.beat)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPES = ("src", "gallery", "topics")

E1 = re.compile(r"\b(manimlib|ShowCreation|TextMobject|TexMobject)\b|^\s*CONFIG\s*=\s*\{", re.M)
E2 = re.compile(r"""["']#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?["']""")
E3 = re.compile(r"\b(MathTex|Tex|SingleStringMathTex)\(\s*r?[\"']")
MANIM_COLOURS = (
    "WHITE|BLACK|GRAY|GREY|LIGHT_GRAY|DARK_GRAY|RED|GREEN|BLUE|YELLOW|GOLD|TEAL|MAROON|PURPLE|"
    "PINK|ORANGE|LIGHT_BROWN|DARK_BROWN|GRAY_BROWN|PURE_RED|PURE_GREEN|PURE_BLUE"
)
E4 = re.compile(rf"\b(?:color|fill_color|stroke_color)\s*=\s*(?:{MANIM_COLOURS})(?:_[A-E])?\b")
W1 = re.compile(r"self\.wait\(\s*[0-9.]+\s*\)")


def lint_source(rel: str, src: str) -> tuple[list[str], list[str]]:
    """Lint source text as if it lived at repo-relative path `rel`. Returns (errors, warnings)."""
    errors, warnings = [], []

    def report(bucket, code, rx, msg):
        for m in rx.finditer(src):
            line = src.count("\n", 0, m.start()) + 1
            bucket.append(f"{rel}:{line}: {code} {msg}: {m.group(0).strip()}")

    report(errors, "E1", E1, "ManimGL API (we use ManimCE)")
    if rel != "src/dsanim/palette.py":
        report(errors, "E2", E2, "hex colour outside palette.py")
    if rel.startswith("topics/"):
        report(errors, "E3", E3, "inline LaTeX; use self.eq('<id>') from script.md")
        report(errors, "E4", E4, "Manim colour constant; use P.<ROLE> from dsanim.palette")
        report(warnings, "W1", W1, "fixed wait; derive timing from self.beat()")
    return errors, warnings


def lint(path: Path) -> tuple[list[str], list[str]]:
    rel = path.resolve().relative_to(ROOT).as_posix()
    return lint_source(rel, path.read_text(encoding="utf-8"))


def in_scope(path: Path) -> bool:
    try:
        rel = path.resolve().relative_to(ROOT)
    except ValueError:
        return False
    return (path.suffix == ".py" and len(rel.parts) > 1 and rel.parts[0] in SCOPES
            and "_template" not in rel.parts and "fixtures" not in rel.parts)


def main() -> int:
    args = sys.argv[1:]
    if args[:1] == ["--hook"]:
        payload = json.loads(sys.stdin.read() or "{}")
        fp = (payload.get("tool_input") or {}).get("file_path") or \
             (payload.get("tool_response") or {}).get("filePath")
        files = [Path(fp)] if fp else []
    elif args:
        files = [Path(a) for a in args]
    else:
        files = [p for s in SCOPES for p in (ROOT / s).rglob("*.py")]

    errors, warnings = [], []
    for f in files:
        if f.exists() and in_scope(f):
            e, w = lint(f)
            errors += e
            warnings += w
    for w in warnings:
        print(w, file=sys.stderr)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        print("AGENTS.md rule violations — fix before continuing.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
