"""Parse script.md — the master document — into scenes, beats, narration and equations.

The format is specified in AGENTS.md §5.1. In short:

    ---
    topic: 030-regression-is-conditional-distribution
    tier: L1
    status: draft            # draft | frozen
    ...
    ---
    ## Scene 3 — "From marginal to conditional"
    ### Beat 3.1
    Ignore weight for a second. [[collapse]] Here is every mpg value we ever saw.

    ```math id=marginal
    Y \\sim \\mathcal{N}(\\mu, \\sigma^2)
    ```

    > Production notes go in blockquotes. They are never spoken.

- Narration = every plain paragraph inside a beat.
- `[[name]]` is a sync mark: silent, it names the moment the following word is spoken.
- ```math id=...``` blocks are the only source of on-screen equations. IDs are unique
  per script.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

SCENE_RE = re.compile(r"^##\s+Scene\s+(\d+)\s*(?:[—–-]\s*(.*))?$")
BEAT_RE = re.compile(r"^###\s+Beat\s+(\d+)\.(\d+)\b\s*(.*)$")
FENCE_OPEN_RE = re.compile(r"^```(\w+)?\s*(.*)$")
MATH_ID_RE = re.compile(r"\bid\s*=\s*([A-Za-z0-9_\-]+)")
MARK_RE = re.compile(r"\[\[([A-Za-z0-9_\-]+)\]\]")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


class ScriptError(ValueError):
    pass


@dataclass
class Equation:
    id: str
    latex: str
    beat: str


@dataclass
class Mark:
    name: str
    word_index: int  # index into the spoken words of the beat; the mark fires as this word starts


@dataclass
class Beat:
    id: str               # "3.2"
    scene: int
    index: int
    title: str
    marked_text: str      # narration with [[marks]] kept
    equations: list[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        """Audio/file key: beat 3.2 -> 's03_b02'."""
        return f"s{self.scene:02d}_b{self.index:02d}"

    @property
    def text(self) -> str:
        """Exactly what is spoken (marks removed, whitespace normalised)."""
        return " ".join(MARK_RE.sub(" ", self.marked_text).split())

    @property
    def words(self) -> list[str]:
        return self.text.split()

    @property
    def marks(self) -> list[Mark]:
        out, count = [], 0
        for token in re.split(r"(\[\[[A-Za-z0-9_\-]+\]\])", self.marked_text):
            m = MARK_RE.fullmatch(token)
            if m:
                out.append(Mark(m.group(1), count))
            else:
                count += len(token.split())
        return out


@dataclass
class SceneSpec:
    number: int
    title: str
    beats: list[str] = field(default_factory=list)


@dataclass
class Script:
    path: Path
    meta: dict
    scenes: dict[int, SceneSpec]
    beats: dict[str, Beat]
    equations: dict[str, Equation]

    @property
    def frozen(self) -> bool:
        return str(self.meta.get("status", "draft")).lower() == "frozen"

    def beat(self, beat_id: str) -> Beat:
        try:
            return self.beats[beat_id]
        except KeyError:
            raise ScriptError(f"{self.path}: no beat {beat_id!r}; have {list(self.beats)}")

    def eq(self, eq_id: str) -> Equation:
        try:
            return self.equations[eq_id]
        except KeyError:
            raise ScriptError(f"{self.path}: no equation id {eq_id!r}; have {list(self.equations)}")


def parse(path: str | Path) -> Script:
    path = Path(path)
    raw = path.read_text(encoding="utf-8")
    meta, body = _split_front_matter(raw, path)
    body = COMMENT_RE.sub("", body)

    scenes: dict[int, SceneSpec] = {}
    beats: dict[str, Beat] = {}
    equations: dict[str, Equation] = {}
    scene: SceneSpec | None = None
    beat: Beat | None = None
    paragraphs: list[str] = []
    fence: dict | None = None

    def flush_beat():
        if beat is not None:
            beat.marked_text = " ".join(" ".join(paragraphs).split())
            paragraphs.clear()

    for lineno, line in enumerate(body.splitlines(), 1):
        if fence is not None:
            if line.strip() == "```":
                if fence["lang"] == "math":
                    if beat is None:
                        raise ScriptError(f"{path}:{lineno}: math block outside a beat")
                    eq = Equation(fence["id"], "\n".join(fence["lines"]).strip(), beat.id)
                    if eq.id in equations:
                        raise ScriptError(f"{path}:{lineno}: duplicate equation id {eq.id!r}")
                    equations[eq.id] = eq
                    beat.equations.append(eq.id)
                fence = None
            else:
                fence["lines"].append(line)
            continue

        if m := FENCE_OPEN_RE.match(line.strip()):
            lang, info = (m.group(1) or ""), m.group(2)
            eq_id = None
            if lang == "math":
                idm = MATH_ID_RE.search(info)
                if not idm:
                    raise ScriptError(f"{path}:{lineno}: ```math block needs id=<name>")
                eq_id = idm.group(1)
            fence = {"lang": lang, "id": eq_id, "lines": []}
            continue

        if m := SCENE_RE.match(line):
            flush_beat()
            beat = None
            n = int(m.group(1))
            if n in scenes:
                raise ScriptError(f"{path}:{lineno}: duplicate Scene {n}")
            scene = scenes[n] = SceneSpec(n, (m.group(2) or "").strip().strip('"'))
            continue

        if m := BEAT_RE.match(line):
            flush_beat()
            s, i = int(m.group(1)), int(m.group(2))
            if scene is None or s != scene.number:
                raise ScriptError(f"{path}:{lineno}: Beat {s}.{i} is not under '## Scene {s}'")
            bid = f"{s}.{i}"
            if bid in beats:
                raise ScriptError(f"{path}:{lineno}: duplicate Beat {bid}")
            beat = beats[bid] = Beat(bid, s, i, m.group(3).strip(), "")
            scene.beats.append(bid)
            continue

        stripped = line.strip()
        if beat is None or not stripped or stripped.startswith((">", "#", "|", "---")):
            continue
        paragraphs.append(stripped)

    if fence is not None:
        raise ScriptError(f"{path}: unclosed code fence")
    flush_beat()
    return Script(path, meta, scenes, beats, equations)


def _split_front_matter(raw: str, path: Path) -> tuple[dict, str]:
    if not raw.startswith("---"):
        return {}, raw
    parts = raw.split("\n---", 1)
    if len(parts) != 2:
        raise ScriptError(f"{path}: front matter not closed with ---")
    meta = yaml.safe_load(parts[0].lstrip("-\n")) or {}
    return meta, parts[1].split("\n", 1)[1] if "\n" in parts[1] else ""
