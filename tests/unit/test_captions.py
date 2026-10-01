import pytest

from dsanim import captions as C

WORDS = "Ignore weight for a second. Here is every mpg value we ever saw.".split()


def test_chunks_respect_max_words():
    groups = C.chunk_words(WORDS, max_words=4, max_chars=100)
    assert all(len(g) <= 4 for g in groups)
    assert [i for g in groups for i in g] == list(range(len(WORDS)))  # every word once, in order


def test_chunks_break_at_sentence_end():
    groups = C.chunk_words(WORDS, max_words=10, max_chars=100)
    assert WORDS[groups[0][-1]] == "second."


def test_chunks_break_at_phrase_boundaries_once_long_enough():
    words = "Pick a weight, say fifteen hundred kilograms: here are the cars.".split()
    groups = C.chunk_words(words, max_words=12, max_chars=100)
    assert [words[g[-1]] for g in groups] == ["weight,", "kilograms:", "cars."]
    short = "Yes, and no.".split()                      # "Yes," is too short to close a card
    assert C.chunk_words(short, max_words=12, max_chars=100) == [[0, 1, 2]]


def test_chunks_respect_max_chars():
    groups = C.chunk_words(["aaaa", "bbbb", "cccc", "dddd"], max_words=10, max_chars=9)
    assert [len(g) for g in groups] == [2, 2]


def test_no_single_word_card_after_punctuation():
    groups = C.chunk_words(["Yes.", "And", "no."], max_words=6)
    assert groups[0] == [0, 1, 2]


def test_captions_chain_and_end_at_duration():
    cards = C.captions_for(WORDS, duration=6.0, max_words=4, max_chars=100)
    assert cards[0].start == 0.0
    assert cards[-1].end == 6.0
    for a, b in zip(cards, cards[1:]):
        assert a.end == b.start


def test_captions_use_word_times_when_aligned():
    times = [{"word": w, "start": 0.5 * i, "end": 0.5 * i + 0.4} for i, w in enumerate(WORDS)]
    cards = C.captions_for(WORDS, duration=7.0, word_times=times, max_words=4, max_chars=100)
    assert cards[1].start == pytest.approx(0.5 * 4)


def test_captions_interpolate_without_word_times():
    cards = C.captions_for(WORDS, duration=13.0, max_words=4, max_chars=100)
    assert cards[1].start == pytest.approx(13.0 * 4 / 13)


def test_captions_empty():
    assert C.captions_for([], 3.0) == []


@pytest.mark.parametrize("t,s", [(0, "00:00:00,000"), (61.5, "00:01:01,500"), (3661.0009, "01:01:01,001")])
def test_srt_timestamp(t, s):
    assert C.srt_timestamp(t) == s


def test_write_srt(tmp_path):
    p = C.write_srt([(0.0, 1.5, "Hello"), (1.5, 3.0, "World")], tmp_path / "x.srt")
    assert p.read_text() == "1\n00:00:00,000 --> 00:00:01,500\nHello\n\n2\n00:00:01,500 --> 00:00:03,000\nWorld\n"
