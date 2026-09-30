---
topic: 030-regression-is-conditional-distribution
tier: L1            # L1 first-contact | L2 practitioner | L3 deep
status: draft             # draft -> frozen (Nitish only). Scenes may not be finalised until frozen.
title_candidates:
  - "Regression is actually a conditional distribution"
  - "You were taught regression wrong"
hook: ""                  # the misconception this video fixes, in one sentence
runtime_target: 9m
wpm: 150                  # your speaking pace; used to estimate timing before any audio exists
tts_voice: af_heart       # placeholder voice (Kokoro); never shipped
tts_speed: 1.0            # calibrate so placeholder durations match your pace
---

> PILOT (AGENTS.md §13): only Scene 3 exists so far. Narration and equations are copied
> verbatim from the Scene 3 shot list in AGENTS.md §5.2. Sync marks [[values]] and
> [[weighs]] were added by the agent (silent; no words changed) — approve or move them.
> Data: dsanim.data.auto_mpg() — UCI Auto MPG, all 398 cars, weight in kg.

## Scene 3 — "From marginal to conditional"

### Beat 3.1
Ignore weight for a second. [[values]] Here is every mpg value we ever saw.

```math id=marginal
Y \sim \mathcal{N}(\mu, \sigma^2)
```

### Beat 3.2
Now suppose I tell you the car [[weighs]] weighs 1500 kg.

```math id=conditional
Y \mid X=x \sim \mathcal{N}(\mu(x), \sigma(x)^2)
```

### Beat 3.3
Slide the weight and the whole distribution moves.
