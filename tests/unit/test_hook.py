"""The script.md approval hook (.claude/hooks/guard_script_md.sh)."""

import json
import subprocess

import pytest

from conftest import ROOT

HOOK = ROOT / ".claude" / "hooks" / "guard_script_md.sh"


def run_hook(path: str) -> str:
    payload = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": path}})
    r = subprocess.run([str(HOOK)], input=payload, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


@pytest.mark.parametrize("path", [
    str(ROOT / "topics/030-x/L1/script.md"),
    "topics/030-x/L1/script.md",
])
def test_topic_script_edits_ask_for_approval(path):
    out = json.loads(run_hook(path))
    assert out["hookSpecificOutput"]["permissionDecision"] == "ask"
    assert path in out["hookSpecificOutput"]["permissionDecisionReason"]


@pytest.mark.parametrize("path", [
    "topics/_template/TIER/script.md", "src/dsanim/scene.py", "gallery/script.md",
    "topics/030-x/L1/shotlist.md",
])
def test_other_files_pass_silently(path):
    assert run_hook(path) == ""


def test_garbage_input_does_not_block():
    r = subprocess.run([str(HOOK)], input="not json", capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip() == ""
