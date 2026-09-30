---
topic: {{concept}}
tier: {{tier}}            # L1 first-contact | L2 practitioner | L3 deep
status: draft             # draft -> frozen (Nitish only). Scenes may not be finalised until frozen.
title_candidates:
  - ""
hook: ""                  # the misconception this video fixes, in one sentence
runtime_target: 9m
wpm: 150                  # your speaking pace; used to estimate timing before any audio exists
tts_voice: af_heart       # placeholder voice (Kokoro); never shipped
tts_speed: 1.0            # calibrate so placeholder durations match your pace
---

<!--
FORMAT (parsed by dsanim.script — keep it exact):
- "## Scene N — "Title""  then  "### Beat N.M"  (M counts from 1 within the scene).
- Plain paragraphs under a beat = narration, spoken verbatim.
- [[name]] inside narration = a silent sync mark ("the band appears as I say 'weighs'").
- ```math id=<name>  blocks = the ONLY on-screen equations. IDs unique in this file.
  Manim's {{ }} splitting syntax is allowed inside for TransformMatchingTex.
- > blockquotes and HTML comments are production notes, never spoken.
Delete this comment and the example below when writing the real script.
-->

## Scene 1 — "Example scene"

### Beat 1.1
This is example narration. When I say [[appear]] this word, something appears.

```math id=example
Y \sim \mathcal{N}(\mu, \sigma^2)
```

> Note: production notes go here and are never spoken.
