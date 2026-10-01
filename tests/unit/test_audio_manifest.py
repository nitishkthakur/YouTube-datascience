import shutil

from conftest import FIXTURES, load_tool, write_tone

am = load_tool("audio_manifest")


def make_tier(tmp_path, monkeypatch):
    tier = tmp_path / "topic" / "L1"
    shutil.copytree(FIXTURES / "topic" / "L1", tier, ignore=shutil.ignore_patterns("renders"))
    audio = tmp_path / "audio"
    monkeypatch.setenv("DSANIM_AUDIO_DIR", str(audio))
    write_tone(audio / "fixture-topic/L1/s01_b01.wav", 1.5)
    write_tone(audio / "fixture-topic/L1/s02_b01.wav", 2.0)
    return tier, audio


def test_register_then_verify_ok(tmp_path, monkeypatch):
    tier, _ = make_tier(tmp_path, monkeypatch)
    entries = am.register(tier)
    assert set(entries) == {"s01_b01", "s02_b01"}
    assert entries["s01_b01"]["duration"] > 1.4 and len(entries["s01_b01"]["wav_sha256"]) == 64
    assert am.verify(tier) == {"s01_b01": "ok", "s02_b01": "ok"}


def test_changed_words_make_a_recording_stale(tmp_path, monkeypatch):
    tier, _ = make_tier(tmp_path, monkeypatch)
    am.register(tier)
    script = tier / "script.md"
    script.write_text(script.read_text().replace("One two three", "One two THREE"))
    assert am.verify(tier)["s01_b01"] == "stale"
    assert am.verify(tier)["s02_b01"] == "ok"


def test_rerecorded_or_deleted_wavs_are_reported(tmp_path, monkeypatch):
    tier, audio = make_tier(tmp_path, monkeypatch)
    am.register(tier)
    write_tone(audio / "fixture-topic/L1/s01_b01.wav", 1.7)
    (audio / "fixture-topic/L1/s02_b01.wav").unlink()
    assert am.verify(tier) == {"s01_b01": "modified", "s02_b01": "missing"}


def test_cli(tmp_path, monkeypatch, capsys):
    tier, _ = make_tier(tmp_path, monkeypatch)
    assert am.main(["register", str(tier)]) == 0
    assert am.main(["verify", str(tier)]) == 0
    assert "all recordings match" in capsys.readouterr().out
