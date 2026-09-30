"""Regression: the parsed structure of known scripts must not change silently.

If a parser change is intentional, regenerate with:
    DSANIM_UPDATE_GOLDEN=1 uv run pytest tests/regression/test_script_golden.py
and review the JSON diff before committing.
"""

import json
import os
from pathlib import Path

import pytest

from conftest import FIXTURES, ROOT
from dsanim.script import parse

GOLDEN = Path(__file__).parent / "golden"
SCRIPTS = {
    "fixture": FIXTURES / "topic/L1/script.md",
    "gallery": ROOT / "gallery/script.md",
}
# The template's front matter holds {{placeholders}}, so it only parses after new_topic.py
# fills them — covered by tests/unit/test_new_topic.py::test_generated_script_parses.


def snapshot(path: Path) -> dict:
    s = parse(path)
    return {
        "meta": s.meta,
        "scenes": {n: {"title": sc.title, "beats": sc.beats} for n, sc in s.scenes.items()},
        "beats": {bid: {"key": b.key, "text": b.text,
                        "marks": [[m.name, m.word_index] for m in b.marks],
                        "equations": b.equations} for bid, b in s.beats.items()},
        "equations": {e.id: {"beat": e.beat, "latex": e.latex} for e in s.equations.values()},
    }


@pytest.mark.regression
@pytest.mark.parametrize("name", list(SCRIPTS))
def test_parse_matches_golden(name):
    got = json.loads(json.dumps(snapshot(SCRIPTS[name]), default=str))
    golden = GOLDEN / f"script_{name}.json"
    if os.environ.get("DSANIM_UPDATE_GOLDEN") == "1" or not golden.exists():
        golden.write_text(json.dumps(got, indent=2, ensure_ascii=False) + "\n")
        if os.environ.get("DSANIM_UPDATE_GOLDEN") != "1":
            pytest.skip(f"created golden {golden.name}; re-run to compare")
    assert got == json.loads(golden.read_text())
