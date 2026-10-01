"""Smoke: agent-facing docs, hooks and skills stay consistent with the code."""

import json
import re

import pytest

from conftest import ROOT

pytestmark = pytest.mark.smoke
NESTED = ["", "src/dsanim", "topics", "tools", "gallery", "tests"]


@pytest.mark.parametrize("folder", NESTED)
def test_agents_md_with_claude_symlink(folder):
    d = ROOT / folder
    assert (d / "AGENTS.md").is_file()
    link = d / "CLAUDE.md"
    assert link.is_symlink() and link.resolve() == (d / "AGENTS.md").resolve()


def test_every_tool_is_documented():
    doc = (ROOT / "tools/AGENTS.md").read_text()
    for tool in (ROOT / "tools").glob("*.py"):
        assert f"`{tool.name}`" in doc, f"{tool.name} missing from tools/AGENTS.md"


def test_root_agents_md_lists_every_tool():
    doc = (ROOT / "AGENTS.md").read_text()
    for tool in (ROOT / "tools").glob("*.py"):
        assert tool.name in doc, f"{tool.name} missing from AGENTS.md §3"


def test_skills_have_matching_frontmatter():
    skills = list((ROOT / ".claude/skills").glob("*/SKILL.md"))
    assert {s.parent.name for s in skills} == {
        "new-topic", "draft-script", "draft-shotlist", "build-scene", "render-review", "narration", "produce"}
    for s in skills:
        m = re.search(r"^---\nname: (\S+)\ndescription: .+\n---", s.read_text(), re.M)
        assert m and m.group(1) == s.parent.name, s


def test_skills_listed_in_agents_md():
    doc = (ROOT / "AGENTS.md").read_text()
    for s in (ROOT / ".claude/skills").iterdir():
        assert f"`{s.name}`" in doc


def test_hooks_reference_existing_scripts():
    settings = json.loads((ROOT / ".claude/settings.json").read_text())
    commands = [h["command"] for ev in settings["hooks"].values() for m in ev for h in m["hooks"]]
    assert any("tools/lint_scenes.py --hook" in c for c in commands)
    assert any("guard_script_md.sh" in c for c in commands)
    assert (ROOT / ".claude/hooks/guard_script_md.sh").stat().st_mode & 0o111


def test_no_stale_lib_references_in_skills_and_nested_docs():
    paths = list((ROOT / ".claude/skills").glob("*/SKILL.md")) + \
        [ROOT / f / "AGENTS.md" for f in NESTED if f]
    for p in paths:
        assert not re.search(r"(?<![\w/])lib/", p.read_text()), p
