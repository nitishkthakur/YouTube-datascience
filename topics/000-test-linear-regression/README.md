# 000-test-linear-regression

**Not a curriculum topic.** A complete, agent-written test video whose job is to run the whole
pipeline — script → placeholder voice → scenes → 480p/720p/1080p → chapters, subtitles,
vertical chunks — and expose gaps before a real topic hits them. Numbered 000 so it sorts first
and never collides with the curriculum (010, 020, …).

| Tier | Audience | Status | Runtime | Link |
|---|---|---|---|---|
| L1 | pipeline test (first-contact level content) | built; placeholder voice; watermarked test renders | ~2.7 min | — |

## Content
Simple linear regression → the line is the conditional mean → the spread it leaves out → you
were predicting a conditional distribution all along → OLS as the special case. It is a
compressed dry run of the real 030 concept and may be mined for it.

## Shared decisions
- dataset: `dsanim.data.auto_mpg()` (UCI Auto MPG, 398 cars, weight in kg), same stage as 030
- OLS fitted on all 398 cars; local fits: Epanechnikov band, half-width 75 kg (`common/stage.py`)
- notation: ŷ = β₀ + β₁x → E[Y|X=x] → Y = β₀ + β₁x + ε → Y|X=x ~ N(β₀+β₁x, σ²) → N(μ(x), σ(x)²)
