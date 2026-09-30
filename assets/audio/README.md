# Narration audio (not in git)

Audio files here are git-ignored. To keep them elsewhere (recommended: a synced/backed-up
folder), set `DSANIM_AUDIO_DIR` in your shell profile; the layout inside is the same.

    <audio root>/<concept>/<tier>/s03_b02.wav                 recorded (wins)
    <audio root>/<concept>/<tier>/placeholder/s03_b02.wav     Kokoro placeholder (never shipped)
    <audio root>/<concept>/<tier>/*.words.json                word timings for [[marks]]
    <audio root>/<concept>/<tier>/raw/scene03.aup3            your Audacity project (optional)

Recording workflow (Audacity): record one take per scene, add a label at each beat boundary
named with the beat key (s03_b01, s03_b02, …), then File → Export → Export Multiple →
"Split files based on: Labels", "Name files: Using Label/Track Name", WAV 48 kHz mono.
