"""Bind Nitish's recordings to the words they were recorded from.

    uv run python tools/audio_manifest.py register <tier_dir>   # after exporting WAVs from Audacity
    uv run python tools/audio_manifest.py verify   <tier_dir>   # what status.py and final renders use

Writes <tier>/audio_manifest.json (committed; the WAVs are not): for every beat with a
recorded WAV, its sha256, duration, and the sha256 of the beat's narration text at the time.
`verify` reports each beat as ok / missing / modified (WAV changed) / stale (the script's
words changed after the recording) — a stale beat fails a final render, because its
[[marks]] and captions would be timed against the wrong words.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import soundfile as sf

from dsanim import narration
from dsanim.script import Script, parse

MANIFEST = "audio_manifest.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def manifest_path(tier: Path) -> Path:
    return tier / MANIFEST


def load(tier: Path) -> dict:
    p = manifest_path(tier)
    return json.loads(p.read_text()) if p.exists() else {}


def register(tier: Path) -> dict:
    script = parse(tier / "script.md")
    d = narration.beat_dir(script)
    entries = {}
    for beat in script.beats.values():
        wav = d / f"{beat.key}.wav"
        if not wav.exists():
            continue
        entries[beat.key] = {
            "beat": beat.id, "wav": wav.name, "wav_sha256": sha256_file(wav),
            "duration": sf.info(str(wav)).duration, "text_sha256": sha256_text(beat.text),
            "text": beat.text, "registered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    manifest_path(tier).write_text(json.dumps({"audio_root": str(d), "beats": entries}, indent=1))
    return entries


def verify_beat(script: Script, key: str, manifest: dict) -> str:
    """ok | missing (WAV gone) | modified (WAV differs) | stale (words changed) | unregistered."""
    entry = (manifest.get("beats") or {}).get(key)
    beat = next((b for b in script.beats.values() if b.key == key), None)
    if entry is None or beat is None:
        return "unregistered"
    wav = narration.beat_dir(script) / entry["wav"]
    if not wav.exists():
        return "missing"
    if sha256_file(wav) != entry["wav_sha256"]:
        return "modified"
    if sha256_text(beat.text) != entry["text_sha256"]:
        return "stale"
    return "ok"


def verify(tier: Path) -> dict[str, str]:
    script = parse(tier / "script.md")
    manifest = load(tier)
    return {key: verify_beat(script, key, manifest) for key in (manifest.get("beats") or {})}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("command", choices=["register", "verify"])
    ap.add_argument("tier", type=Path)
    args = ap.parse_args(argv)
    tier = args.tier.resolve()
    if args.command == "register":
        entries = register(tier)
        print(f"registered {len(entries)} recording(s) in {manifest_path(tier)}")
        for k, e in entries.items():
            print(f"  {k}  {e['duration']:5.2f}s  {e['wav_sha256'][:8]}")
        return 0
    results = verify(tier)
    if not results:
        print(f"no {MANIFEST} in {tier} (run `register` after exporting recordings)")
        return 0
    bad = 0
    for k, r in results.items():
        print(f"  {k}  {r}")
        bad += r != "ok"
    print("all recordings match the script" if not bad else f"{bad} recording(s) need attention")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
