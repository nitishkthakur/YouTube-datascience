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


def test_subset_render_merges_into_existing_manifest(tmp_path, monkeypatch):
    manifest = render_all.manifest_path(tmp_path, "l", False)
    manifest.parent.mkdir(parents=True)
    (tmp_path / "scenes").mkdir()
    fa, fb, fgone = (tmp_path / "scenes" / n for n in ("s01_a.py", "s02_b.py", "s03_gone.py"))
    fa.write_text("class A(DSScene): pass\n")
    fb.write_text("class B(DSScene): pass\n")
    manifest.write_text(json.dumps({"scenes": [
        {"file": str(fa), "scene_number": 1, "class": "A", "mp4": "a.mp4", "duration": 1.0},
        {"file": str(fb), "scene_number": 2, "class": "B", "mp4": "b.mp4", "duration": 2.0},
        {"file": str(fgone), "scene_number": 3, "class": "Gone", "mp4": "g.mp4", "duration": 3.0}]}))
    monkeypatch.setattr(render_all, "render_one", lambda e, *a: {**e, "mp4": "b2.mp4", "beats_json": None, "duration": 9.0, "log": ""})
    render_all.main([str(tmp_path), "-q", "l", "--scenes", "s02_b.py"])
    scenes = json.loads(manifest.read_text())["scenes"]
    # B updated, A kept, the deleted scene dropped
    assert [(s["class"], s["duration"]) for s in scenes] == [("A", 1.0), ("B", 9.0)]


def test_inputs_hash_changes_with_scene_file_and_quality(tmp_path):
    tier = tmp_path / "topic" / "L1"
    (tier / "scenes").mkdir(parents=True)
    (tier / "script.md").write_text("---\ntopic: t\ntier: L1\n---\n## Scene 1 — x\n### Beat 1.1\nhi\n")
    f = tier / "scenes" / "s01_a.py"
    f.write_text("class A(DSScene): pass\n")
    entry = {"file": str(f), "scene_number": 1, "class": "A"}
    h1 = render_all.inputs_hash(entry, tier, "l", False)
    assert h1 == render_all.inputs_hash(entry, tier, "l", False)
    assert h1 != render_all.inputs_hash(entry, tier, "m", False)
    assert h1 != render_all.inputs_hash(entry, tier, "l", True)
    f.write_text("class A(DSScene): x = 1\n")
    assert h1 != render_all.inputs_hash(entry, tier, "l", False)


def test_render_one_skips_unchanged_scene(tmp_path, monkeypatch):
    tier = tmp_path / "topic" / "L1"
    (tier / "scenes").mkdir(parents=True)
    (tier / "renders").mkdir()
    (tier / "script.md").write_text("---\ntopic: t\ntier: L1\n---\n")
    f = tier / "scenes" / "s01_a.py"
    f.write_text("class A(DSScene): pass\n")
    entry = {"file": str(f), "scene_number": 1, "class": "A"}
    (tier / "renders" / "A_l.mp4").write_bytes(b"x")
    (tier / "renders" / "A_l.beats.json").write_text("{}")
    (tier / "renders" / "A_l.inputs.sha").write_text(render_all.inputs_hash(entry, tier, "l", False))
    monkeypatch.setattr(render_all, "probe_duration", lambda p: 1.0)
    monkeypatch.setattr(render_all.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(AssertionError("should not render")))
    r = render_all.render_one(entry, "l", False, False, False)
    assert r["skipped"] and r["duration"] == 1.0
    (tier / "renders" / "A_l.inputs.sha").write_text("stale")
    with pytest.raises(AssertionError, match="should not render"):
        render_all.render_one(entry, "l", False, False, False)
