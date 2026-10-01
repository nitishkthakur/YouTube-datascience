"""Every topic tier in the repo: script parses, scenes reference only existing beats/equations,
scene files follow the sNN_ naming, and the shot list carries a Status line."""

import re

import pytest

from conftest import ROOT, load_tool
from dsanim.script import parse

render_all = load_tool("render_all")
TIERS = sorted(p.parent for p in ROOT.glob("topics/[0-9]*/*/script.md"))
EQ_REF = re.compile(r"self\.eq\(\s*[\"']([A-Za-z0-9_\-]+)[\"']")
BEAT_REF = re.compile(r"self\.beat\(\s*[\"'](\d+\.\d+)[\"']")


@pytest.mark.parametrize("tier", TIERS, ids=[f"{t.parent.name}/{t.name}" for t in TIERS])
def test_tier_is_consistent(tier):
    script = parse(tier / "script.md")
    assert script.meta["topic"] == tier.parent.name and script.meta["tier"] == tier.name
    entries = render_all.discover(tier)
    for e in entries:
        assert e["scene_number"] in script.scenes, f"{e['file']}: no Scene {e['scene_number']} in script"
        src = open(e["file"]).read()
        for eid in EQ_REF.findall(src):
            assert eid in script.equations, f"{e['file']}: self.eq({eid!r}) not in script"
        for bid in BEAT_REF.findall(src):
            assert bid in script.beats, f"{e['file']}: self.beat({bid!r}) not in script"
            assert int(bid.split(".")[0]) == e["scene_number"], f"{e['file']} plays beat {bid} of another scene"
    if (tier / "shotlist.md").exists():
        assert re.search(r"^Status:\s*\w+", (tier / "shotlist.md").read_text(), re.M)
