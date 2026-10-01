# Narration audio (not in git)

Audio files here are git-ignored. To keep them elsewhere (recommended: a synced/backed-up
folder), put `DSANIM_AUDIO_DIR=/path` in `<repo>/.env` (see `.env.example`) — not in your
shell profile, which tools, hooks and agents do not see. `tools/status.py` prints the resolved
root on its first line.

    <audio root>/<concept>/<tier>/s03_b02.wav                 recorded (wins)
    <audio root>/<concept>/<tier>/placeholder/s03_b02.wav     Kokoro placeholder (never shipped)
    <audio root>/<concept>/<tier>/*.words.json                word timings for [[marks]]
    <audio root>/<concept>/<tier>/raw/scene03.aup3            your Audacity project (optional)

`<concept>` is the full folder name including its number, e.g.
`030-regression-is-conditional-distribution`; `<tier>` is `L1`, `L2` or `L3`.

## Recording spec
- WAV, 48 kHz, mono, 24-bit PCM. Peaks at or below −6 dBFS; noise floor below −60 dBFS.
- One take per scene in Audacity; a **point label** at the start of each beat, named with the
  beat key (`s03_b01`, `s03_b02`, …). Leave ≥ 0.3 s of room before the first word of a beat and
  ≤ 1 s after its last word — the scene adds its own 0.5 s tail, so do not pad.
- Export: Audacity 3.4+: *File → Export Audio → Export Multiple* (3.3 and earlier: *File →
  Export → Export Multiple*): split by **labels**, name files by **label**, WAV 24-bit.
- Re-take one beat: re-record and re-export only that label; overwriting the WAV is enough.
- Then register: `uv run python tools/audio_manifest.py register <tier_dir>`. This writes
  `<tier>/audio_manifest.json` (committed) binding each WAV to the words it was recorded from.
  If the script's words change afterwards, `status.py` reports that beat as **stale** and a final
  render refuses it until it is re-recorded (or the words restored).
- Changing a word after freezing: set `status: draft` in script.md, make the edit, re-freeze,
  re-record the affected beats, re-register.
