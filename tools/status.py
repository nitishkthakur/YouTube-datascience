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
import importlib.util
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

from dsanim import narration
from dsanim.script import ScriptError, parse

ROOT = Path(__file__).resolve().parents[1]
QUALITIES = {"l": "480p15", "m": "720p30", "h": "1080p60"}


def _tool(name):
    spec = importlib.util.spec_from_file_location(f"tools_{name}", Path(__file__).with_name(f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


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

    items.append(Item("NITISH", "audio root", True, str(narration.beat_dir(script)),
                      "set DSANIM_AUDIO_DIR in .env to move it"))
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
    if recorded:
        am = _tool("audio_manifest")
        states = am.verify(tier)
        if not states:
            items.append(Item("NITISH", "recordings registered (audio_manifest.json)", False, "none",
                              f"uv run python tools/audio_manifest.py register {tier}"))
        else:
            bad = {k: v for k, v in states.items() if v != "ok"}
            items.append(Item("NITISH", "recordings match the script's words", not bad,
                              ", ".join(f"{k}: {v}" for k, v in bad.items()) or f"{len(states)} ok",
                              "stale = words changed after recording: re-record that beat or restore the words; "
                              "modified = re-register"))
    items.append(Item("CODE", "placeholder audio for beats without a recording",
                      None if recorded == n else (missing == 0),
                      f"{placeholder} placeholder, {missing} missing",
                      f"uv run --extra tts python tools/tts_placeholder.py {tier}"))

    shot = tier / "shotlist.md"
    state, detail = ("none", "no shotlist.md")
    if shot.exists():
        state, detail = _tool("approve").approval_state(shot.read_text())
    items.append(Item("AGENT", "shotlist.md drafted", shot.exists() and state != "none",
                      detail, "skill draft-shotlist"))
    items.append(Item("NITISH", "shotlist.md approved and unchanged since", state == "approved",
                      {"approved": "approved", "edited": "edited after approval", "unbound": detail,
                       "draft": f"Status: {detail}", "none": detail}[state],
                      f"read shotlist.md, then `uv run python tools/approve.py {tier}` (binds the approval to the text)"))

    files = scene_files(tier)
    wanted = sorted(script.scenes)
    have = [s for s in wanted if s in files]
    items.append(Item("AGENT", "a scene file for every script scene", len(have) == len(wanted),
                      f"{len(have)}/{len(wanted)}: missing {[s for s in wanted if s not in files]}",
                      "skill build-scene (one scene at a time)"))

    renders = tier / "renders"
    classes = {}
    for f in (tier / "scenes").glob("s*.py"):
        m = re.search(r"^class\s+(\w+)\s*\(\s*DSScene\s*\)", f.read_text(), re.M)
        if m:
            classes[f.name] = m.group(1)
    for q, label in QUALITIES.items():
        present = [c for c in classes.values() if (renders / f"{c}_{q}.mp4").exists()]
        items.append(Item("CODE", f"scene renders {label}", len(present) == len(wanted) if wanted else None,
                          f"{len(present)}/{len(wanted)} scenes on disk",
                          f"uv run python tools/render_all.py {tier} -q {q}"))
    chunks = tier / "shorts" / "chunks.yaml"
    chunk_list = (yaml.safe_load(chunks.read_text()) or {}).get("chunks", []) if chunks.exists() else []
    needed_v = sorted({f for c in chunk_list for f in c.get("scenes", [])})
    have_v = [f for f in needed_v if f in classes and (renders / f"{classes[f]}_h_v.mp4").exists()]
    items.append(Item("CODE", "vertical 1080x1920 renders for the scenes the chunks use",
                      (len(have_v) == len(needed_v)) if needed_v else None,
                      f"{len(have_v)}/{len(needed_v)}" if needed_v else "no chunks declared",
                      f"uv run python tools/make_shorts.py {tier} -q h"))
    sheets = [p for p in renders.glob("*_m.sheet.png") if renders.exists()
              and (p.with_name(p.name.replace(".sheet.png", ".mp4")).exists()
                   and p.stat().st_mtime >= p.with_name(p.name.replace(".sheet.png", ".mp4")).stat().st_mtime - 1)]
    items.append(Item("CODE", "contact sheets at 720p exist and are newer than their renders",
                      len(sheets) >= len(wanted) if wanted else None,
                      f"{len(sheets)} sheets for {len(wanted)} scenes", "render_all.py -q m --sheet"))
    notes_text = (tier / "NOTES.md").read_text() if (tier / "NOTES.md").exists() else ""
    reviewed = [p.name for p in sheets if p.name in notes_text or p.name.replace("_m.sheet.png", "") in notes_text]
    items.append(Item("AGENT", "sheet inspection logged in NOTES.md (names each reviewed sheet)",
                      (len(reviewed) >= len(wanted)) if wanted else None,
                      f"{len(reviewed)}/{len(wanted)} sheets mentioned", "skill render-review, then log the sheet names"))

    topic, tname = script.meta.get("topic", tier.parent.name), script.meta.get("tier", tier.name)
    for q, label in QUALITIES.items():
        out = renders / f"{topic}_{tname}_{q}.mp4"
        items.append(Item("CODE", f"assembled video {label}", out.exists() if renders.exists() else None,
                          str(out.name), f"uv run python tools/assemble.py {tier} -q {q}"))
    publish = tier / "publish"
    items.append(Item("CODE", "chapters.txt + subtitles.srt", (publish / "chapters.txt").exists()
                      and (publish / "subtitles.srt").exists(), "", "produced by assemble.py"))

    items.append(Item("NITISH", "shorts/chunks.yaml (which beats become vertical chunks)",
                      chunks.exists() or None, "optional" if not chunks.exists() else f"{len(chunk_list)} declared",
                      "list chunks (tools/make_shorts.py docstring); an agent can propose them"))
    if chunk_list:
        names = [c["name"] for c in chunk_list]
        made = [n for n in names if (renders / "shorts" / f"{n}_h.mp4").exists()]
        items.append(Item("CODE", "vertical chunks rendered (1080x1920)", len(made) == len(names),
                          f"{len(made)}/{len(names)}", f"uv run python tools/make_shorts.py {tier} -q h"))

    desc = publish / "description.md"
    desc_text = desc.read_text() if desc.exists() else ""
    title = re.search(r"^title:\s*(.+)$", desc_text, re.M)
    items.append(Item("NITISH", "publish/description.md: title chosen", bool(title and title.group(1).strip().strip('"')),
                      title.group(1).strip() if title else "no `title:` line",
                      "put `title: ...` at the top of publish/description.md (script.md only lists candidates)"))
    filled = bool(desc_text) and "<!--" not in desc_text.split("## Chapters")[0]
    items.append(Item("NITISH", "publish/description.md written", filled, "", "fill the description (hook, links); chapters are pasted from chapters.txt"))
    thumb = any((publish / f"thumbnail.{ext}").exists() for ext in ("png", "jpg", "jpeg"))
    items.append(Item("NITISH", "publish/thumbnail.png chosen (1280x720 min, 16:9, < 2 MB)", thumb, "",
                      "a frame that states the misconception + 3-5 big words (AGENTS.md §11); an agent can propose 3"))
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
