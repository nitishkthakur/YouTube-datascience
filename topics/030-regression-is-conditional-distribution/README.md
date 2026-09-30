# 030-regression-is-conditional-distribution

One concept, several videos. Each tier folder (L1/, L2/, L3/) is one complete video with
its own script, shot list, scenes and renders.

| Tier | Audience | Status | Runtime | Link |
|---|---|---|---|---|
| L1 | first contact | pilot: Scene 3 built, awaiting narration recording | 9m target | |
| L2 | practitioner | not started | | |

## Depends on
- 010 distributions, 020 conditional-distributions (channel/curriculum.md)

## Shared decisions across tiers
- dataset(s): `dsanim.data.auto_mpg()` — UCI Auto MPG, all 398 cars, weight in **kg** (converted
  from lb), mpg as recorded. Axes: weight 500–2500 kg, mpg 0–50.
- notation (keep identical across tiers): Y = mpg, X = weight; marginal Y ~ N(μ, σ²);
  conditional Y | X = x ~ N(μ(x), σ(x)²). Conditional fits are local band estimates
  (Epanechnikov, half-width 75 kg) so σ(x) is real, not assumed constant; OLS is introduced
  later as the special case μ(x) linear, σ(x) constant.
- colour roles: data DATA, band + "x = 1500 kg" PARAM, distributions CONCEPT, mean trace MODEL.
