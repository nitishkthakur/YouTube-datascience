import pytest

from dsanim.script import ScriptError, parse


def test_front_matter(fixture_script):
    s = parse(fixture_script)
    assert s.meta["topic"] == "fixture-topic" and s.meta["tier"] == "L1"
    assert s.frozen


def test_scenes_and_beats(fixture_script):
    s = parse(fixture_script)
    assert list(s.scenes) == [1, 2]
    assert s.scenes[1].title == "Timing"
    assert s.scenes[1].beats == ["1.1", "1.2"]
    assert list(s.beats) == ["1.1", "1.2", "2.1"]
    assert s.beat("1.2").title == "optional title"


def test_beat_key_names_audio_files(fixture_script):
    assert parse(fixture_script).beat("2.1").key == "s02_b01"


def test_narration_strips_marks_notes_and_math(fixture_script):
    b = parse(fixture_script).beat("1.1")
    assert b.text == "One two three four five six."
    assert "production note" not in b.text and "mathcal" not in b.text


def test_marks_record_word_positions(fixture_script):
    s = parse(fixture_script)
    assert [(m.name, m.word_index) for m in s.beat("1.1").marks] == [("go", 3)]
    assert [(m.name, m.word_index) for m in s.beat("2.1").marks] == [("a", 1), ("b", 2)]


def test_equations_by_id(fixture_script):
    s = parse(fixture_script)
    eq = s.eq("fixture-eq")
    assert eq.beat == "1.1"
    assert eq.latex == r"Y \mid X = x \sim \mathcal{N}({{\mu(x)}}, \sigma^2)"
    assert s.beat("1.1").equations == ["fixture-eq"]


def test_unknown_ids_raise(fixture_script):
    s = parse(fixture_script)
    with pytest.raises(ScriptError):
        s.beat("9.9")
    with pytest.raises(ScriptError):
        s.eq("nope")


def _write(tmp_path, body, meta="topic: t\ntier: L1\n"):
    p = tmp_path / "script.md"
    p.write_text(f"---\n{meta}---\n{body}")
    return p


@pytest.mark.parametrize("body,msg", [
    ("## Scene 1 — x\n### Beat 1.1\nhi\n```math\na\n```\n", "needs id"),
    ("## Scene 1 — x\n### Beat 1.1\nhi\n```math id=a\na\n```\n```math id=a\nb\n```\n", "duplicate equation"),
    ("### Beat 1.1\nhi\n", "not under"),
    ("## Scene 1 — x\n### Beat 2.1\nhi\n", "not under"),
    ("## Scene 1 — x\n### Beat 1.1\nhi\n### Beat 1.1\nagain\n", "duplicate Beat"),
    ("## Scene 1 — x\n## Scene 1 — y\n", "duplicate Scene"),
    ("## Scene 1 — x\n### Beat 1.1\nhi\n```math id=a\nunclosed\n", "unclosed"),
    ("```math id=a\nx\n```\n", "outside a beat"),
])
def test_malformed_scripts_are_rejected(tmp_path, body, msg):
    with pytest.raises(ScriptError, match=msg):
        parse(_write(tmp_path, body))


def test_html_comments_are_ignored(tmp_path):
    s = parse(_write(tmp_path, "## Scene 1 — x\n### Beat 1.1\nsaid <!-- not said --> aloud\n"))
    assert s.beat("1.1").text == "said aloud"


def test_draft_is_default_status(tmp_path):
    assert not parse(_write(tmp_path, "")).frozen


def test_non_math_code_blocks_are_not_narration(tmp_path):
    s = parse(_write(tmp_path, "## Scene 1 — x\n### Beat 1.1\nspoken\n```python\nx = 1\n```\n"))
    assert s.beat("1.1").text == "spoken" and not s.equations
