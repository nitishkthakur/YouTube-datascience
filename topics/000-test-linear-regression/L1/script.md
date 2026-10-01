---
topic: 000-test-linear-regression
tier: L1
status: draft             # TEST VIDEO: agent-written to exercise the pipeline end to end. Not for publication.
title_candidates:
  - "The regression line is a conditional mean — and that's the small part"
  - "What the regression line actually claims"
hook: "You think regression predicts a number; it predicts a whole distribution, and the line is only its centre."
runtime_target: 3m
wpm: 150
tts_voice: af_heart
tts_speed: 1.0
---

> TEST VIDEO. Narration written by the agent (Nitish is not recording this one). Its purpose is
> to run the whole pipeline — script → placeholder voice → five scenes → 480p/720p/1080p →
> chapters, subtitles, vertical chunks — and find the gaps. Data: UCI Auto MPG, all 398 cars,
> weight in kg (dsanim.data.auto_mpg). OLS line: mpg = β₀ + β₁·weight fitted to all 398 cars.

## Scene 1 — "A line through the cloud"

### Beat 1.1
Here are three hundred and ninety-eight cars: [[cars]] how heavy each one is, and how far it goes on a gallon of fuel.

### Beat 1.2
Linear regression fits one straight line through this cloud. [[line]] You have seen this equation a thousand times.

```math id=line
\hat{y} = \beta_0 + \beta_1 x
```

### Beat 1.3
But what is the line actually claiming? Not that every car sits on it. They clearly do not.

## Scene 2 — "The line is a conditional mean"

### Beat 2.1
Pick a weight. Say [[band]] fifteen hundred kilograms. Here are the cars near that weight.

### Beat 2.2
Average their fuel economy, [[mean]] and you get one number. That number is what the line is trying to be.

### Beat 2.3
Slide the weight, [[slide]] and the averages trace a path. The line is the straight-line guess for that path: the mean of y, given x.

```math id=condmean
\mathbb{E}[Y \mid X=x] = \beta_0 + \beta_1 x
```

### Beat 2.4
Close. Not exact. Remember that.

## Scene 3 — "What the line leaves out"

### Beat 3.1
Now look at the cars near fifteen hundred again. [[residuals]] Each one misses the line by some amount. Regression calls these residuals.

### Beat 3.2
Their spread has a name too: [[sigma]] sigma. The textbook writes it as noise added to the line.

```math id=noise
Y = \beta_0 + \beta_1 x + \varepsilon ,\qquad \varepsilon \sim \mathcal{N}(0, \sigma^2)
```

### Beat 3.3
But that word, noise, hides the point. The spread is not an error. It is part of the prediction.

## Scene 4 — "You were predicting a distribution all along"

### Beat 4.1
Put the two together. At each weight, a centre from the line and a spread from sigma: [[bell]] that is a whole bell curve, one per weight.

```math id=ols
Y \mid X=x \sim \mathcal{N}(\beta_0 + \beta_1 x, \sigma^2)
```

### Beat 4.2
Ordinary least squares assumes every bell has the same width. [[sweep]] Slide along, and watch the real cars disagree: the spread shrinks as they get heavier.

### Beat 4.3
So the honest statement is this. [[general]] Given x, y has a distribution. Its centre moves with x, and so does its spread. The line was only ever the centre.

```math id=general
Y \mid X=x \sim \mathcal{N}(\mu(x), \sigma(x)^2)
```

## Scene 5 — "Regression, restated"

### Beat 5.1
Regression is not predicting a number. [[dist]] It is predicting a conditional distribution. [[ols]] Ordinary least squares is the special case where that distribution is Normal, its width is constant, and you only model the centre.

### Beat 5.2
[[next]] Everything that follows in this series is about dropping those three assumptions, one at a time.
