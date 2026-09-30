# src/dsanim — the visual language

Everything every video shares. A change here changes every past and future video, so work
deliberately. Root AGENTS.md §3–§4 and §14 apply; this file adds the local rules.

## Module map
| Module | Owns | Don't |
|---|---|---|
| `palette.py` | every colour, semantic role, font name, type size, motion default | put a colour or font anywhere else |
| `layout.py` | orientation (`DSANIM_VERTICAL`), safe area, `plot/equation/caption` regions | position things with magic coordinates in scenes |
| `typography.py` | `text()`, `label()`, `code()`, `math()`, XeLaTeX STIX template, vertical text scale | construct `Text`/`MathTex` with styling elsewhere |
| `script.py` | parsing `script.md` (format: root AGENTS.md §5.1) | loosen the format silently — it is a contract with Nitish |
| `narration.py` | locating beat audio, durations, `[[mark]]` times | read audio paths anywhere else |
| `scene.py` | `DSScene`: `self.beat()`, `self.eq()`, `self.layout`, `self.vertical`; global Manim config on import | add per-topic logic |
| `data.py` | every dataset shown on screen (real loaders + seeded synthetic generators with docstrings) | generate data inside a scene |
| `stats.py` | every estimator whose result is drawn (Normal MLE, Epanechnikov local Normal fit) | compute statistics ad hoc in a scene |
| `components/gaussian.py` | `GaussianSlice`: a Normal density on its side along x = x0, with `mean_line()` / `sigma_segment()` | vary its height by density — slices share one `peak_width` (shape, not height) |
| `components/scatter.py` | `Scatter`: dots that remember their data; `collapsed()`, `focus_band()`, `unfocus()` | |
| `components/conditional.py` | `band()`, `conditional_slice()`, `mean_point()` — the conditioning mechanics | |
| `components/ledger.py` | `Ledger`: live `symbol = value unit` readouts bound to callables (`.live()` during sweeps) | |
| `components/equations.py` | `reveal()` terms at marks, `morph()` old→new keeping surviving terms in place | glyph-morph with TransformMatchingShapes |
| `captions.py` | caption cards from narration + word timings (burned into vertical renders; SRT) | |
| `env.py` | `render_env()`: subprocess environment with TeX on PATH | duplicate PATH logic in tools/tests |

## Rules
- Components take colours as **roles** (`P.CONCEPT`, …) and sizes from `palette`; they size themselves from a `layout.Region` rather than absolute units, so they work in both orientations.
- Components never call `self.wait`/`self.play` with hard-coded durations tied to narration; they return mobjects/animations and let the scene time them with `b.until(...)`.
- Every new or changed public function gets unit tests. A new component also gets a `gallery/` scene; a major one also gets a golden-frame regression test (root AGENTS.md §14).
- Changing `palette.py`/`layout.py`/`typography.py` or a component changes the gallery goldens: re-render the affected `gallery/` scene(s), inspect them, then regenerate goldens deliberately (`tests/regression/test_gallery_frames.py`).
- `Create(slice.curve)` / `FadeIn(slice.fill)` add the *submobjects* to the scene; to take a `GaussianSlice` off screen remove `.curve` and `.fill` as well as the group (or animate the group as a whole).
- ManimCE 0.21 API only. If unsure, check the installed version's source/docs; never guess from ManimGL examples.
