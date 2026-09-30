"""Generate PLACEHOLDER narration for every beat of a script with Kokoro-82M (Apache-2.0).

    uv run --extra tts python tools/tts_placeholder.py <tier_dir> [--beats 3.1 3.2]
                                                       [--voice af_heart] [--speed 1.0]

Writes <audio_root>/<topic>/<tier>/placeholder/<key>.wav plus <key>.words.json (word start/
end times, used to resolve [[marks]]). Placeholders exist so animation timing can be built
before Nitish records; they are never shipped (renders at -qh/-qk refuse them).

Voice/speed can be set per script in front matter (tts_voice, tts_speed). Calibrate
tts_speed so placeholder durations match Nitish's natural pace.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import warnings
from pathlib import Path

import numpy as np
import soundfile as sf

from dsanim import narration
from dsanim.script import parse

SR = 24_000
PUNCT = re.compile(r"^\W+$")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("target", type=Path)
    ap.add_argument("--beats", nargs="*")
    ap.add_argument("--voice")
    ap.add_argument("--speed", type=float)
    args = ap.parse_args()

    warnings.filterwarnings("ignore")
    from kokoro import KPipeline  # heavy import; only needed here

    path = args.target / "script.md" if args.target.is_dir() else args.target
    script = parse(path)
    voice = args.voice or script.meta.get("tts_voice", "af_heart")
    speed = args.speed or float(script.meta.get("tts_speed", 1.0))
    out_dir = narration.beat_dir(script) / "placeholder"
    out_dir.mkdir(parents=True, exist_ok=True)
    pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")

    for bid, beat in script.beats.items():
        if args.beats and bid not in args.beats:
            continue
        chunks, words, offset = [], [], 0.0
        for result in pipe(beat.text, voice=voice, speed=speed):
            audio = result.audio.cpu().numpy() if hasattr(result.audio, "cpu") else result.audio
            for tok in result.tokens or []:
                if PUNCT.match(tok.text) or tok.start_ts is None:
                    continue
                words.append({"word": tok.text, "start": offset + tok.start_ts,
                              "end": offset + (tok.end_ts or tok.start_ts)})
            chunks.append(audio)
            offset += len(audio) / SR
        wav = np.concatenate(chunks)
        dest = out_dir / f"{beat.key}.wav"
        sf.write(dest, wav, SR)
        words_file = dest.with_suffix(".words.json")
        if len(words) == len(beat.words):
            words_file.write_text(json.dumps(words, indent=1))
            note = "word timings ok"
        else:
            words_file.unlink(missing_ok=True)
            note = f"word count mismatch ({len(words)} vs {len(beat.words)}); marks interpolate"
        print(f"{bid:>5} {dest.name}  {len(wav) / SR:5.2f}s  PLACEHOLDER  ({note})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
