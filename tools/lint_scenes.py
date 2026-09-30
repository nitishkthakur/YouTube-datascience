"""Mechanical enforcement of AGENTS.md rules that agents most often break.

    uv run python tools/lint_scenes.py [files...]     # no args: lint the whole repo
    uv run python tools/lint_scenes.py --hook         # Claude Code hook: tool-call JSON on stdin

Exit 0 = clean (warnings may print), exit 2 = violations (the hook feeds them back to Claude).

Rules
  everywhere (src/, gallery/, topics/):
    E0  file does not parse
    E1  ManimGL-isms: manimlib, ShowCreation, TextMobject, TexMobject, CONFIG dicts
    E2  hex colour literals outside src/dsanim/palette.py
  topic scenes (topics/**.py), checked on the AST so variables and f-strings don't slip past:
    E3  MathTex/Tex/typography.math() call — equations come from self.eq("<id>") in script.md;
        single diagram symbols from typography.symbol("mu")
    E4  a Manim colour constant (BLUE, RED_E, ...) anywhere — use dsanim.palette roles (P.MODEL)
    W1  self.wait(<literal or variable>) — timing comes from the beat tracker (b.until / b.wait_until)
"""

from __future__ import annotations

import ast
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPES = ("src", "gallery", "topics")

E1 = re.compile(r"\b(manimlib|ShowCreation|TextMobject|TexMobject)\b|^\s*CONFIG\s*=\s*\{", re.M)
E2 = re.compile(r"""["']#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?["']""")
_BASE_COLOURS = (
    "WHITE BLACK GRAY GREY LIGHT_GRAY LIGHT_GREY DARK_GRAY DARK_GREY LIGHTER_GRAY DARKER_GRAY "
    "RED GREEN BLUE YELLOW GOLD TEAL MAROON PURPLE PINK ORANGE LIGHT_PINK LIGHT_BROWN DARK_BROWN "
    "GRAY_BROWN PURE_RED PURE_GREEN PURE_BLUE"
).split()
MANIM_COLOURS = set(_BASE_COLOURS) | {f"{c}_{s}" for c in _BASE_COLOURS for s in "ABCDE"}
TEX_CALLS = {"MathTex", "Tex", "SingleStringMathTex"}


def _call_name(node: ast.Call) -> tuple[str | None, str | None]:
    """('math', 'T') for T.math(...); ('MathTex', None) for MathTex(...)."""
    fn = node.func
    if isinstance(fn, ast.Name):
        return fn.id, None
    if isinstance(fn, ast.Attribute):
        base = fn.value.id if isinstance(fn.value, ast.Name) else None
        return fn.attr, base
    return None, None


def topic_rules(rel: str, src: str) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return [f"{rel}:{e.lineno}: E0 does not parse: {e.msg}"], []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name, base = _call_name(node)
            if name in TEX_CALLS or (name == "math" and base in ("T", "typography")):
                errors.append(f"{rel}:{node.lineno}: E3 inline equation via {name}(); "
                              "use self.eq('<id>') from script.md (or typography.symbol for one symbol)")
            if name == "wait" and base == "self" and node.args \
                    and isinstance(node.args[0], (ast.Constant, ast.Name)):
                warnings.append(f"{rel}:{node.lineno}: W1 fixed self.wait(); "
                                "derive timing from the beat tracker (b.until / b.wait_until / b.remaining)")
        elif isinstance(node, ast.Name) and node.id in MANIM_COLOURS:
            errors.append(f"{rel}:{node.lineno}: E4 Manim colour constant {node.id}; use P.<ROLE> from dsanim.palette")
    return errors, warnings


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
        e, w = topic_rules(rel, src)
        errors += e
        warnings += w
    return errors, warnings


def lint(path: Path, root: Path = ROOT) -> tuple[list[str], list[str]]:
    rel = path.resolve().relative_to(root).as_posix()
    return lint_source(rel, path.read_text(encoding="utf-8"))


def in_scope(path: Path, root: Path = ROOT) -> bool:
    try:
        rel = path.resolve().relative_to(root)
    except ValueError:
        return False
    return (path.suffix == ".py" and len(rel.parts) > 1 and rel.parts[0] in SCOPES
            and "_template" not in rel.parts and "fixtures" not in rel.parts)


def main(argv: list[str] | None = None, root: Path = ROOT, stdin: io.TextIOBase | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    stdin = stdin or sys.stdin
    if args[:1] == ["--hook"]:
        payload = json.loads(stdin.read() or "{}")
        fp = (payload.get("tool_input") or {}).get("file_path") or \
             (payload.get("tool_response") or {}).get("filePath")
        files = [Path(fp)] if fp else []
    elif args:
        files = [Path(a) for a in args]
    else:
        files = [p for s in SCOPES for p in (root / s).rglob("*.py")]

    errors, warnings = [], []
    for f in files:
        if f.exists() and in_scope(f, root):
            e, w = lint(f, root)
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
