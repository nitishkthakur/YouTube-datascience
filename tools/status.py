"""Readiness report for a tier: what Nitish must provide, what the code makes, what is done.

    uv run python tools/status.py <tier_dir> [--json]

Every line names who supplies it:
    NITISH  — only he can: script, narration recordings, approvals, thumbnail, description
    CODE    — deterministic tools produce it from his inputs (tools/pipeline.py)
    AGENT   — judgement work an agent does and records (contact-sheet review, NOTES)
Exit 0 always; read the "next" list at the end.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from dsanim import narration
from dsanim.script import ScriptError, parse

ROOT = Path(__file__).resolve().parents[1]
QUALITIES = {"l": "480p15", "m": "720p30", "h": "1080p60"}


@dataclass
class Item:
    who: str        # NITISH | CODE | AGENT
    label: str
    ok: bool | None  # None = not applicable / optional
    detail: str = ""
    how: str = ""    # what to do if not ok


def scene_files(tier: Path) -> dict[int, Path]:
    out = {}
    for f in sorted((tier / "scenes").glob("s*.py")):
        m = re.match(r"^s(\d{2})_", f.name)
        if m:
            out[int(m.group(1))] = f
    return out


def report(tier: Path) -> list[Item]:
    items: list[Item] = []
    script_path = tier / "script.md"
    try:
        script = parse(script_path)
    except (ScriptError, FileNotFoundError) as e:
        return [Item("NITISH", "script.md parses", False, str(e), "fix the script format (AGENTS.md §5.1)")]

    frozen = script.frozen
    items.append(Item("NITISH", "script.md parses", True, f"{len(script.scenes)} scenes, {len(script.beats)} beats"))
    items.append(Item("NITISH", "script.md frozen (status: frozen)", frozen,
                      f"status: {script.meta.get('status', 'draft')}",
                      "set `status: frozen` in the front matter once narration and equations are final"))

    recorded = placeholder = missing = 0
    for b in script.beats.values():
        try:
            a = narration.load(script, b)
        except ValueError as e:
            items.append(Item("NITISH", "audio location", False, str(e), "front matter needs topic and tier"))
            break
        if a.kind == "recorded":
            recorded += 1
        elif a.kind == "placeholder":
            placeholder += 1
        else:
            missing += 1
    n = len(script.beats)
    items.append(Item("NITISH", "narration recorded for every beat", recorded == n and n > 0,
                      f"{recorded} recorded, {placeholder} placeholder, {missing} missing of {n}",
                      f"record in Audacity, export one WAV per beat to {narration.beat_dir(script)} "
                      "(assets/audio/README.md)"))
    items.append(Item("CODE", "placeholder audio for beats without a recording",
                      None if recorded == n else (missing == 0),
                      f"{placeholder} placeholder, {missing} missing",
                      f"uv run --extra tts python tools/tts_placeholder.py {tier}"))

    shot = tier / "shotlist.md"
    shot_status = None
    if shot.exists():
        m = re.search(r"^Status:\s*(\w+)", shot.read_text(), re.M)
        shot_status = m.group(1).lower() if m else None
    items.append(Item("AGENT", "shotlist.md drafted", shot.exists() and shot_status is not None,
                      f"Status: {shot_status}", "skill draft-shotlist"))
    items.append(Item("NITISH", "shotlist.md approved (Status: approved)", shot_status == "approved",
                      f"Status: {shot_status}", "review shotlist.md and set `Status: approved`"))

    files = scene_files(tier)
    wanted = sorted(script.scenes)
    have = [s for s in wanted if s in files]
    items.append(Item("AGENT", "a scene file for every script scene", len(have) == len(wanted),
                      f"{len(have)}/{len(wanted)}: missing {[s for s in wanted if s not in files]}",
                      "skill build-scene (one scene at a time)"))

    renders = tier / "renders"
    for q, label in QUALITIES.items():
        for vertical in (False, True):
            tag = f"{q}{'_v' if vertical else ''}"
            manifest = renders / f"manifest_{tag}.json"
            ok = None
            detail = "not rendered"
            if manifest.exists():
                scenes = json.loads(manifest.read_text())["scenes"]
                present = [s for s in scenes if Path(s["mp4"]).exists()]
                ok = len(present) == len(wanted)
                detail = f"{len(present)}/{len(wanted)} scenes"
            if not vertical or q != "k":
                items.append(Item("CODE", f"scene renders {label}{' vertical' if vertical else ''}", ok, detail,
                                  f"uv run python tools/render_all.py {tier} -q {q}{' --vertical' if vertical else ''}"))
    sheets = [p for p in renders.glob("*_m.sheet.png")] if renders.exists() else []
    items.append(Item("AGENT", "contact sheets at 720p inspected (renders/*_m.sheet.png)",
                      len(sheets) >= len(wanted) if wanted else None,
                      f"{len(sheets)} sheets for {len(wanted)} scenes", "skill render-review"))

    topic, tname = script.meta.get("topic", tier.parent.name), script.meta.get("tier", tier.name)
    for q, label in QUALITIES.items():
        out = renders / f"{topic}_{tname}_{q}.mp4"
        items.append(Item("CODE", f"assembled video {label}", out.exists() if renders.exists() else None,
                          str(out.name), f"uv run python tools/assemble.py {tier} -q {q}"))
    publish = tier / "publish"
    items.append(Item("CODE", "chapters.txt + subtitles.srt", (publish / "chapters.txt").exists()
                      and (publish / "subtitles.srt").exists(), "", "produced by assemble.py"))

    chunks = tier / "shorts" / "chunks.yaml"
    items.append(Item("NITISH", "shorts/chunks.yaml (which beats become vertical chunks)",
                      chunks.exists() or None, "optional" if not chunks.exists() else "declared",
                      "list chunks (tools/make_shorts.py docstring); an agent can propose them"))
    if chunks.exists():
        import yaml
        names = [c["name"] for c in (yaml.safe_load(chunks.read_text()) or {}).get("chunks", [])]
        made = [n for n in names if (renders / "shorts" / f"{n}_h.mp4").exists()]
        items.append(Item("CODE", "vertical chunks rendered (1080x1920)", len(made) == len(names),
                          f"{len(made)}/{len(names)}", f"uv run python tools/make_shorts.py {tier} -q h"))

    desc = publish / "description.md"
    filled = desc.exists() and "<!--" not in desc.read_text().split("## Chapters")[0]
    items.append(Item("NITISH", "publish/description.md written", filled, "", "fill the description (title, hook, links)"))
    thumb = any((publish / f"thumbnail.{ext}").exists() for ext in ("png", "jpg", "jpeg"))
    items.append(Item("NITISH", "publish/thumbnail.png chosen", thumb, "",
                      "pick a frame that states the misconception (AGENTS.md §11); an agent can propose 3"))
    notes = tier / "NOTES.md"
    logged = notes.exists() and len(notes.read_text().split("## Log", 1)[-1].strip()) > 0
    items.append(Item("AGENT", "NOTES.md has a log", logged, "", "append decisions, breakages, render times"))
    return items


def render_text(items: list[Item]) -> str:
    mark = {True: "✓", False: "✗", None: "–"}
    lines = []
    for who in ("NITISH", "CODE", "AGENT"):
        lines.append(f"\n{who}")
        for it in items:
            if it.who == who:
                detail = f"  ({it.detail})" if it.detail else ""
                lines.append(f"  {mark[it.ok]} {it.label}{detail}")
    todo = [it for it in items if it.ok is False]
    lines.append("\nnext")
    if not todo:
        lines.append("  nothing missing")
    for it in todo:
        lines.append(f"  [{it.who}] {it.label}: {it.how}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("tier", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    items = report(args.tier.resolve())
    if args.json:
        print(json.dumps([asdict(i) for i in items], indent=1))
    else:
        print(f"readiness — {args.tier}")
        print(render_text(items))
    return 0


if __name__ == "__main__":
    sys.exit(main())
