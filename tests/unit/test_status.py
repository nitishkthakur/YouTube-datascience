import shutil

from conftest import FIXTURES, load_tool

status = load_tool("status")


def by_label(items):
    return {i.label: i for i in items}


def test_fixture_tier_report(tmp_path, monkeypatch):
    monkeypatch.setenv("DSANIM_AUDIO_DIR", str(tmp_path / "none"))
    tier = tmp_path / "topic" / "L1"
    shutil.copytree(FIXTURES / "topic" / "L1", tier, ignore=shutil.ignore_patterns("renders"))
    items = by_label(status.report(tier))
    assert items["script.md parses"].ok
    assert items["script.md frozen (status: frozen)"].ok
    assert items["narration recorded for every beat"].ok is False
    assert items["a scene file for every script scene"].ok  # s01_timing.py, s02_second.py
    assert items["shotlist.md approved (Status: approved)"].ok is False
    assert items["scene renders 480p15"].ok is None  # not rendered yet
    text = status.render_text(list(items.values()))
    assert "NITISH" in text and "next" in text and "record in Audacity" in text


def test_broken_script_is_reported_not_raised(tmp_path):
    tier = tmp_path / "t" / "L1"
    tier.mkdir(parents=True)
    (tier / "script.md").write_text("---\ntopic: t\ntier: L1\n---\n### Beat 1.1\nx\n")
    items = status.report(tier)
    assert len(items) == 1 and items[0].ok is False and items[0].who == "NITISH"


def test_who_labels_are_only_the_three_roles(tmp_path, monkeypatch):
    monkeypatch.setenv("DSANIM_AUDIO_DIR", str(tmp_path / "none"))
    assert {i.who for i in status.report(FIXTURES / "topic" / "L1")} <= {"NITISH", "CODE", "AGENT"}
