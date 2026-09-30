import shutil

import pytest

from conftest import ROOT, load_tool

new_topic = load_tool("new_topic")


@pytest.fixture
def fake_root(tmp_path):
    shutil.copytree(ROOT / "topics" / "_template", tmp_path / "topics" / "_template")
    return tmp_path


def test_creates_concept_and_tier(fake_root):
    assert new_topic.main(["030-regression-demo", "L1"], root=fake_root) == 0
    tier = fake_root / "topics/030-regression-demo/L1"
    for f in ["script.md", "shotlist.md", "NOTES.md", "publish/description.md"]:
        assert (tier / f).exists(), f
    assert (tier / "scenes").is_dir() and (tier / "shorts").is_dir()
    script = (tier / "script.md").read_text()
    assert "topic: 030-regression-demo" in script and "tier: L1" in script
    assert "{{concept}}" not in (fake_root / "topics/030-regression-demo/README.md").read_text()


def test_second_tier_reuses_concept(fake_root):
    new_topic.main(["030-regression-demo", "L1"], root=fake_root)
    assert new_topic.main(["030-regression-demo", "L2"], root=fake_root) == 0
    assert (fake_root / "topics/030-regression-demo/L2/script.md").exists()


def test_refuses_to_overwrite(fake_root):
    new_topic.main(["030-regression-demo", "L1"], root=fake_root)
    with pytest.raises(SystemExit):
        new_topic.main(["030-regression-demo", "L1"], root=fake_root)


@pytest.mark.parametrize("concept,tier", [("30-bad", "L1"), ("030_Bad", "L1"), ("030-ok", "L9")])
def test_validates_names(fake_root, concept, tier):
    with pytest.raises(SystemExit):
        new_topic.main([concept, tier], root=fake_root)


def test_generated_script_parses(fake_root):
    from dsanim.script import parse
    new_topic.main(["030-regression-demo", "L1"], root=fake_root)
    s = parse(fake_root / "topics/030-regression-demo/L1/script.md")
    assert s.meta["tier"] == "L1" and "1.1" in s.beats
