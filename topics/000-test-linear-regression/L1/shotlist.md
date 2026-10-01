# Shot list — 000-test-linear-regression / L1 (TEST VIDEO)

Agent-drafted, agent-approved (this tier exists to test the pipeline; Nitish is not recording
it). Narration is quoted from script.md. `extend` = silent visual time past the speech.
Colour roles: DATA grey, PARAM amber (the chosen weight), MODEL violet (the line),
CONCEPT teal (the conditional centre / spread), ERROR coral (residuals).

Status: approved

Persistent across ALL scenes (common/stage.py): axes weight 500–2500 kg × mpg 0–50, 398 cars
(DATA), equation panel right (upper: equation; lower: live ledger). Scene N's end state is
scene N+1's first frame — assemble.py reports every seam.

## Scene 1 — "A line through the cloud" (~17s)
Layout: plot-left-60 / eq-right-40

### Beat 1.1 (speech ~6s · extend 1s)
NARRATION: "Here are three hundred and ninety-eight cars: [[cars]] how heavy each one is, and how far it goes on a gallon of fuel."
FOCUS: the cloud of cars
- axes fade in from the start; at [[cars]] the 398 dots fade in over 1.5 s
STATE: chart, scatter
TRANSITION: hold

### Beat 1.2 (speech ~6s · extend 1s)
NARRATION: "Linear regression fits one straight line through this cloud. [[line]] You have seen this equation a thousand times."
FOCUS: the line being drawn
- at [[line]]: OLS line drawn left→right (1.2 s), MODEL; equation `line` written, terms coloured by role
STATE: chart, scatter, line, eq line
TRANSITION: hold

### Beat 1.3 (speech ~5s · extend 0.5s)
NARRATION: "But what is the line actually claiming? Not that every car sits on it. They clearly do not."
FOCUS: the gap between dots and line
- Indicate the line (pulse, MODEL) on "claiming"; nothing else moves
STATE: chart, scatter, line, eq line
TRANSITION: identical to Scene 2's first frame

## Scene 2 — "The line is a conditional mean" (~34s)

### Beat 2.1 (speech ~5s · extend 1.5s)
NARRATION: "Pick a weight. Say [[band]] fifteen hundred kilograms. Here are the cars near that weight."
FOCUS: the band
- at [[band]]: band at 1500 kg (150 kg wide, PARAM) with label "1500 kg"; cars inside → DATA_FOCUS, rest fade to 35%
STATE: + band, label, focused scatter
TRANSITION: hold

### Beat 2.2 (speech ~6s · extend 1.5s)
NARRATION: "Average their fuel economy, [[mean]] and you get one number. That number is what the line is trying to be."
FOCUS: the in-band cars collapsing to one dot
- at [[mean]]: the in-band cars slide horizontally onto the band's centre line (0.8 s) — the same
  "collapse" verb the channel uses for "ignore x" — then a CONCEPT dot grows at their mean
- ledger appears: x = 1500 kg (PARAM), μ(x) = 19.7 (CONCEPT), ŷ = 20.9 (MODEL)
STATE: + mean dot, ledger; in-band cars collapsed
TRANSITION: cars spring back at the start of 2.3

### Beat 2.3 (speech ~8s · extend 6s)
NARRATION: "Slide the weight, [[slide]] and the averages trace a path. The line is the straight-line guess for that path: the mean of y, given x."
FOCUS: the CONCEPT dot tracing a path along the line
- in-band cars spring back (0.6 s); label fades (the ledger's x replaces it)
- at [[slide]]: band slides 1500 → 900 kg (1.5 s, smooth) then 900 → 2200 kg (5 s, linear); focus and
  mean dot follow; the dot leaves a CONCEPT trace; ledger updates live
- equation morphs `line` → `condmean`: ŷ becomes E[Y | X=x]; β₀ + β₁ x stays in place
STATE: band at 2200, trace 900–2200, ledger, eq condmean
TRANSITION: hold

### Beat 2.4 (speech ~3s · extend 1.5s)
NARRATION: "Close. Not exact. Remember that."
FOCUS: trace vs line
- Indicate the trace; then band, trace, dot, ledger fade out and the scatter unfocuses
STATE: chart, scatter, line, eq condmean
TRANSITION: identical to Scene 3's first frame

## Scene 3 — "What the line leaves out" (~26s)

### Beat 3.1 (speech ~7s · extend 1.5s)
NARRATION: "Now look at the cars near fifteen hundred again. [[residuals]] Each one misses the line by some amount. Regression calls these residuals."
FOCUS: the residual sticks
- band at 1500 reappears, cars focus (same as 2.1, no label); at [[residuals]] a vertical stick from
  each in-band car to the line (ERROR), lagged 1 s
STATE: + band, sticks
TRANSITION: hold

### Beat 3.2 (speech ~6s · extend 2s)
NARRATION: "Their spread has a name too: [[sigma]] sigma. The textbook writes it as noise added to the line."
FOCUS: the σ bracket
- at [[sigma]]: bracket ±σ (OLS residual sd = 4.3) beside the band around the line, labelled σ (CONCEPT)
- equation morphs `condmean` → `noise`: E[Y | X=x] becomes Y; "+ ε, ε ~ N(0, σ²)" appears (ε ERROR)
STATE: + bracket, eq noise
TRANSITION: hold

### Beat 3.3 (speech ~6s · extend 1s)
NARRATION: "But that word, noise, hides the point. The spread is not an error. It is part of the prediction."
FOCUS: the bracket, not the sticks
- on "not an error": sticks fade; the bracket pulses
STATE: chart, focused scatter, line, band, bracket, eq noise
TRANSITION: identical to Scene 4's first frame

## Scene 4 — "You were predicting a distribution all along" (~36s)

### Beat 4.1 (speech ~8s · extend 1.5s)
NARRATION: "Put the two together. At each weight, a centre from the line and a spread from sigma: [[bell]] that is a whole bell curve, one per weight."
FOCUS: the bell growing out of the band
- at [[bell]]: OLS slice at 1500 (centre = line, width = σ), bulging right, MODEL; bracket fades into it
- equation morphs `noise` → `ols`
STATE: + OLS slice, eq ols
TRANSITION: hold

### Beat 4.2 (speech ~9s · extend 8s)
NARRATION: "Ordinary least squares assumes every bell has the same width. [[sweep]] Slide along, and watch the real cars disagree: the spread shrinks as they get heavier."
FOCUS: two bells — the rigid one and the real one
- at [[sweep]]: a second slice, the LOCAL fit (CONCEPT, bulging left), appears in the same band
- band slides 1500 → 900 (1.5 s) then 900 → 2200 (5.5 s); both slices follow; ledger: x, σ (constant 4.3), σ(x) (local, changing), n
STATE: band at 2200, both slices, ledger
TRANSITION: hold

### Beat 4.3 (speech ~10s · extend 1.5s)
NARRATION: "So the honest statement is this. [[general]] Given x, y has a distribution. Its centre moves with x, and so does its spread. The line was only ever the centre."
FOCUS: the equation
- at [[general]]: equation morphs `ols` → `general` (β₀ + β₁ x → μ(x); σ → σ(x)); the local slice pulses; on "only ever the centre" the line pulses
STATE: everything of 4.2 + eq general
TRANSITION: Scene 5 fades the plot to the background

## Scene 5 — "Regression, restated" (~24s)

### Beat 5.1 (speech ~14s · extend 1s)
NARRATION: "Regression is not predicting a number. [[dist]] It is predicting a conditional distribution. [[ols]] Ordinary least squares is the special case where that distribution is Normal, its width is constant, and you only model the centre."
FOCUS: the three summary lines
- plot side fades out (an end card, no text over faded ticks); line 1 "Regression predicts a conditional distribution." at [[dist]];
  line 2 "OLS: Normal, constant width, centre only." at [[ols]]; eq general stays on the right
STATE: two text lines, eq general
TRANSITION: hold

### Beat 5.2 (speech ~5s · extend 2s)
NARRATION: "[[next]] Everything that follows in this series is about dropping those three assumptions, one at a time."
FOCUS: line 3
- line 3 "Next: drop those assumptions, one at a time." at [[next]]; hold 2 s
STATE: end card
TRANSITION: end of video

## Shorts (shorts/chunks.yaml)
- `the-line-is-a-conditional-mean`: Scene 2 whole (34 s)
- `what-the-line-leaves-out`: Scene 3 from beat 3.2 through Scene 4 beat 4.2 (~33 s)
