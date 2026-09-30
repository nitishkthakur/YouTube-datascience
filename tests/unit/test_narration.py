import json

import pytest

from conftest import write_tone
from dsanim import narration
from dsanim.script import parse


def test_no_audio_estimates_from_wpm(fixture_script, audio_dir):
    s = parse(fixture_script)
    a = narration.load(s, s.beat("1.1"))
    assert a.kind == "silent-estimate" and a.path is None
    assert a.duration == pytest.approx(6 / 120 * 60)  # 6 words at wpm=120


def test_placeholder_is_found_and_flagged(fixture_script, audio_dir):
    s = parse(fixture_script)
    write_tone(audio_dir / "fixture-topic/L1/placeholder/s01_b01.wav", 2.0)
    a = narration.load(s, s.beat("1.1"))
    assert a.placeholder and a.kind == "placeholder"
    assert a.duration == pytest.approx(2.0, abs=0.01)


def test_recorded_audio_wins_over_placeholder(fixture_script, audio_dir):
    s = parse(fixture_script)
    write_tone(audio_dir / "fixture-topic/L1/placeholder/s01_b01.wav", 2.0)
    write_tone(audio_dir / "fixture-topic/L1/s01_b01.wav", 3.0)
    a = narration.load(s, s.beat("1.1"))
    assert a.kind == "recorded" and a.duration == pytest.approx(3.0, abs=0.01)


def test_mark_time_interpolates_without_word_timings(fixture_script, audio_dir):
    s = parse(fixture_script)
    write_tone(audio_dir / "fixture-topic/L1/s01_b01.wav", 6.0)
    a = narration.load(s, s.beat("1.1"))
    assert a.mark_time("go") == pytest.approx(6.0 * 3 / 6, abs=0.01)


def test_mark_time_uses_word_timings_when_available(fixture_script, audio_dir):
    s = parse(fixture_script)
    wav = write_tone(audio_dir / "fixture-topic/L1/s01_b01.wav", 6.0)
    words = [{"word": w, "start": 0.5 * i, "end": 0.5 * i + 0.4}
             for i, w in enumerate(s.beat("1.1").words)]
    wav.with_suffix(".words.json").write_text(json.dumps(words))
    a = narration.load(s, s.beat("1.1"))
    assert a.mark_time("go") == pytest.approx(1.5)  # 4th word starts at 1.5 s


def test_mismatched_word_timings_fall_back_to_interpolation(fixture_script, audio_dir):
    s = parse(fixture_script)
    wav = write_tone(audio_dir / "fixture-topic/L1/s01_b01.wav", 6.0)
    wav.with_suffix(".words.json").write_text(json.dumps([{"word": "x", "start": 0, "end": 1}]))
    assert narration.load(s, s.beat("1.1")).mark_time("go") == pytest.approx(3.0, abs=0.01)


def test_unknown_mark_raises(fixture_script, audio_dir):
    s = parse(fixture_script)
    with pytest.raises(KeyError):
        narration.load(s, s.beat("1.1")).mark_time("nope")


def test_missing_topic_or_tier_is_an_error(tmp_path, audio_dir):
    p = tmp_path / "script.md"
    p.write_text("---\ntopic: t\n---\n## Scene 1 — x\n### Beat 1.1\nhi\n")
    s = parse(p)
    with pytest.raises(ValueError, match="tier"):
        narration.load(s, s.beat("1.1"))


def test_audio_root_defaults_to_repo_assets(monkeypatch):
    monkeypatch.delenv("DSANIM_AUDIO_DIR", raising=False)
    assert narration.audio_root() == narration.repo_root() / "assets" / "audio"
