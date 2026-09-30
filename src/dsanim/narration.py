"""Find and measure the audio for a beat; resolve sync marks to times.

Audio lives OUTSIDE git (AGENTS.md §7). Lookup order for beat 3.2 of topic T, tier L:

    $DSANIM_AUDIO_DIR/T/L/s03_b02.wav                (recorded by Nitish — wins)
    $DSANIM_AUDIO_DIR/T/L/placeholder/s03_b02.wav    (Kokoro TTS draft — never shipped)
    (nothing)                                        -> silent, duration estimated from WPM

DSANIM_AUDIO_DIR defaults to <repo>/assets/audio (git-ignored).

Word timings, when available, sit next to the audio as `<key>.words.json`:
    [{"word": "Ignore", "start": 0.12, "end": 0.41}, ...]
Placeholders get them for free from Kokoro; recorded audio gets them from forced alignment
(tools/align.py, not yet built). Without them, a mark's time is interpolated by word position.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

import soundfile as sf

from dsanim.script import Beat, Script

DEFAULT_WPM = 150.0  # used only when there is no audio at all; calibrate from Nitish's voice


def repo_root(start: Path | None = None) -> Path:
    p = (start or Path(__file__)).resolve()
    for parent in [p, *p.parents]:
        if (parent / "pyproject.toml").exists() and (parent / "topics").exists():
            return parent
    raise FileNotFoundError("could not locate repo root (pyproject.toml + topics/)")


def audio_root() -> Path:
    env = os.environ.get("DSANIM_AUDIO_DIR")
    return Path(env).expanduser() if env else repo_root() / "assets" / "audio"


def beat_dir(script: Script) -> Path:
    topic, tier = script.meta.get("topic"), script.meta.get("tier")
    if not topic or not tier:
        raise ValueError(f"{script.path}: front matter needs 'topic' and 'tier'")
    return audio_root() / str(topic) / str(tier)


@dataclass
class BeatAudio:
    beat: Beat
    path: Path | None
    duration: float          # seconds of narration (audio length, or WPM estimate)
    placeholder: bool
    word_times: list[dict] | None

    @property
    def kind(self) -> str:
        return "recorded" if self.path and not self.placeholder else (
            "placeholder" if self.path else "silent-estimate")

    def mark_time(self, name: str) -> float:
        """Seconds from the start of the beat audio at which mark `name` fires."""
        marks = {m.name: m.word_index for m in self.beat.marks}
        if name not in marks:
            raise KeyError(f"beat {self.beat.id} has no mark [[{name}]]; has {list(marks)}")
        idx, n = marks[name], max(len(self.beat.words), 1)
        if self.word_times and len(self.word_times) == len(self.beat.words):
            return self.word_times[idx]["start"] if idx < n else self.duration
        return self.duration * idx / n


def load(script: Script, beat: Beat) -> BeatAudio:
    d = beat_dir(script)
    for path, placeholder in ((d / f"{beat.key}.wav", False),
                              (d / "placeholder" / f"{beat.key}.wav", True)):
        if path.exists():
            words_file = path.with_suffix(".words.json")
            words = json.loads(words_file.read_text()) if words_file.exists() else None
            return BeatAudio(beat, path, sf.info(str(path)).duration, placeholder, words)
    wpm = float(script.meta.get("wpm", DEFAULT_WPM))
    return BeatAudio(beat, None, len(beat.words) / wpm * 60.0, False, None)
