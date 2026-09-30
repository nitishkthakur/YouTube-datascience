# Curriculum

The order concepts must be taught in, because each depends on the ones before it
(AGENTS.md §1). Folder numbers are gapped by 10 so a concept can be inserted later without
renaming (e.g. 035 between 030 and 040). **Proposed — Nitish to confirm or reorder.**

| # | Concept (folder slug) | Depends on | Tiers planned | Status |
|---|---|---|---|---|
| 010 | distributions | — | L1 | idea |
| 020 | conditional-distributions | 010 | L1 | idea |
| 030 | regression-is-conditional-distribution | 020 | L1, L2 | **pilot: Scene 3 built (placeholder voice); -qh waits on recording** |
| 040 | likelihood | 010, 030 | L1, L2 | idea |
| 050 | entropy-and-cross-entropy | 040 | L1, L2 | idea |
| 060 | maximum-entropy-families | 050 | L2, L3 | idea |
| 070 | glms | 030, 040, 060 | L1, L2 | idea |
| 080 | trees-and-ensembles | 030 | L1, L2 | idea |
| 090 | anomaly-detection | 020, 040 | L1, L2 | idea |
| 100 | explainability | 080 | L1, L2 | idea |

## Datasets in use
- `dsanim.data.auto_mpg()` — the familiar one (mpg vs weight). Pilot.
- `dsanim.data.fuel_economy()` — the fresh one (2020+ cars, mpg vs engine size). Same
  question fifty years later; curved mean and shrinking spread set up 070-glms.
