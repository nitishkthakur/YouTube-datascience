"""Captions: split a beat's narration into short timed cards.

Used twice: burned into vertical renders (AGENTS.md §10, the caption band) and written as
SRT subtitles for uploads (tools/assemble.py). Timing comes from the beat's word timings
when they exist (Kokoro placeholders, or a forced alignment of the recording) and is
otherwise interpolated by word position.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

MAX_WORDS = 6    # per card — read at a glance on a phone
MAX_CHARS = 36   # per card — fits the caption band at SIZE_CAPTION in vertical
SENTENCE_END = ".!?;"


@dataclass(frozen=True)
class Caption:
    text: str
    start: float  # seconds from the start of the beat's audio
    end: float


def chunk_words(words: list[str], max_words: int = MAX_WORDS, max_chars: int = MAX_CHARS
                ) -> list[list[int]]:
    """Greedy split into groups of consecutive word indices.

    A group closes when adding a word would exceed max_words/max_chars, or after sentence
    punctuation (so cards follow the phrasing) unless that would leave a single-word card.
    """
    groups: list[list[int]] = []
    cur: list[int] = []
    chars = 0
    for i, w in enumerate(words):
        if cur and (len(cur) >= max_words or chars + 1 + len(w) > max_chars):
            groups.append(cur)
            cur, chars = [], 0
        cur.append(i)
        chars += len(w) + (1 if chars else 0)
        if w[-1] in SENTENCE_END and len(cur) >= 2:
            groups.append(cur)
            cur, chars = [], 0
    if cur:
        groups.append(cur)
    return groups


def captions_for(words: list[str], duration: float, word_times: list[dict] | None = None,
                 **chunk_kw) -> list[Caption]:
    """Timed cards for one beat. The first card starts at 0; each ends when the next starts;
    the last ends at `duration` (the speech length)."""
    if not words:
        return []
    groups = chunk_words(words, **chunk_kw)
    aligned = bool(word_times) and len(word_times) == len(words)
    starts = [word_times[g[0]]["start"] if aligned else duration * g[0] / len(words)
              for g in groups]
    starts[0] = 0.0
    out = []
    for k, g in enumerate(groups):
        end = starts[k + 1] if k + 1 < len(groups) else duration
        out.append(Caption(" ".join(words[i] for i in g), starts[k], max(end, starts[k])))
    return out


def srt_timestamp(t: float) -> str:
    ms = int(round(max(t, 0.0) * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(entries: list[tuple[float, float, str]], path: str | Path) -> Path:
    """entries: (start, end, text) in seconds from the start of the video, in order."""
    lines = []
    for n, (start, end, text) in enumerate(entries, 1):
        lines += [str(n), f"{srt_timestamp(start)} --> {srt_timestamp(end)}", text, ""]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
