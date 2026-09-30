import json

import pytest

from conftest import FIXTURES, ROOT, load_tool

render_all = load_tool("render_all")
TIER = FIXTURES / "topic" / "L1"


def test_discover_orders_by_scene_number_and_ignores_other_files():
    entries = render_all.discover(TIER)
    assert [(e["scene_number"], e["class"]) for e in entries] == [(1, "Scene01"), (2, "Scene02")]
    assert all("timing_scene" not in e["file"] for e in entries)


def test_discover_requires_exactly_one_scene_class(tmp_path):
    (tmp_path / "scenes").mkdir()
    (tmp_path / "scenes" / "s01_a.py").write_text("class A(DSScene): pass\nclass B(DSScene): pass\n")
    with pytest.raises(SystemExit, match="exactly one"):
        render_all.discover(tmp_path)


def test_unknown_scene_filter_is_an_error():
    with pytest.raises(SystemExit, match="unknown scene files"):
        render_all.main([str(TIER), "-q", "l", "--scenes", "s99_nope.py"])


@pytest.mark.slow
def test_render_all_writes_manifest(tmp_path, monkeypatch):
    monkeypatch.setenv("DSANIM_AUDIO_DIR", str(tmp_path / "none"))
    manifest = render_all.main([str(TIER), "-q", "l", "--jobs", "2"])
    data = json.loads(manifest.read_text())
    assert [s["class"] for s in data["scenes"]] == ["Scene01", "Scene02"]
    for s in data["scenes"]:
        assert s["duration"] > 0.5 and s["beats_json"] and (ROOT / s["mp4"]).exists()
