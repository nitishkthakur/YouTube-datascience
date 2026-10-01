"""BeatTracker in isolation, with a fake scene clock (no rendering)."""

import types
import warnings

import pytest
from manim import config

from conftest import FIXTURES
from dsanim import narration
from dsanim.scene import BeatTracker, frames
from dsanim.script import parse


class FakeScene:
    def __init__(self):
        self.renderer = types.SimpleNamespace(time=0.0)

    def wait(self, t):
        self.renderer.time += t


@pytest.fixture
def beat():
    return parse(FIXTURES / "topic/L1/script.md").beat("1.1")  # 6 words, [[go]] before word 4


def audio_for(beat, duration=4.0, word_times=None):
    return narration.BeatAudio(beat, None, duration, False, word_times)


def test_frames_rounds_up_to_whole_frames():
    fps = config.frame_rate
    assert frames(1 / fps) == pytest.approx(1 / fps)
    assert frames(1.0001 / fps) == pytest.approx(2 / fps)
    assert frames(0.0) == 0.0


def test_budget_remaining_and_elapsed(beat):
    s = FakeScene()
    t = BeatTracker(s, audio_for(beat), extend=1.5)
    assert t.duration == 4.0 and t.budget == 5.5 and t.remaining == 5.5
    s.wait(2.0)
    assert t.elapsed == 2.0 and t.remaining == 3.5


def test_until_returns_time_to_mark_and_records_it(beat):
    s = FakeScene()
    t = BeatTracker(s, audio_for(beat))
    dt = t.until("go")                     # mark at word 3 of 6 -> 2.0 s
    assert dt == pytest.approx(frames(2.0))
    assert t.marks_hit["go"]["hit"] == pytest.approx(dt) and not t.marks_hit["go"]["late"]


def test_until_warns_and_floors_when_past_the_mark(beat):
    s = FakeScene()
    t = BeatTracker(s, audio_for(beat))
    s.wait(3.0)
    with pytest.warns(UserWarning, match="past"):
        assert t.until("go") == pytest.approx(frames(0.1))
    assert t.marks_hit["go"]["late"]


def test_wait_until_advances_the_clock_and_warns_when_late(beat):
    s = FakeScene()
    t = BeatTracker(s, audio_for(beat))
    t.wait_until("go")
    assert s.renderer.time == pytest.approx(frames(2.0))
    assert t.marks_hit["go"] == {"hit": pytest.approx(frames(2.0)), "late": False}
    s.wait(1.0)
    with pytest.warns(UserWarning, match="late"):
        t.wait_until("go")


def test_wait_until_uses_word_timings(beat):
    times = [{"word": w, "start": 0.5 * i, "end": 0.5 * i + 0.4} for i, w in enumerate(beat.words)]
    s = FakeScene()
    t = BeatTracker(s, audio_for(beat, word_times=times))
    t.wait_until("go")
    assert s.renderer.time == pytest.approx(frames(1.5))


def test_no_warning_when_on_time(beat):
    s = FakeScene()
    t = BeatTracker(s, audio_for(beat))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        t.until("go")
