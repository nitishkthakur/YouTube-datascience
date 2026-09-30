# gallery — review scenes for dsanim components

One scene per component, plus `style_sheet.py` (palette roles, type, an equation, layout
regions) and `conditional_components.py` (GaussianSlice, Scatter, band, conditional slice,
mean trace on synthetic data). They are how Nitish and agents *see* the visual language, and
they back the golden-frame regression tests. A new gallery scene is registered in
`tests/regression/test_gallery_frames.py::SCENES`.

- `script.md` here is test-fixture narration (not channel content); `topic: gallery`,
  `tier: style`, so placeholder audio goes to `<audio root>/gallery/style/`.
- Render: `uv run python tools/render.py gallery/<file>.py <Scene> -q m --sheet [--vertical]`.
- After any change to `palette.py`, `layout.py` or `typography.py`: render the style sheet in
  both orientations, inspect the contact sheets, then (only if the change is intended)
  `DSANIM_UPDATE_GOLDEN=1 uv run pytest tests/regression/test_gallery_frames.py` and
  look at the new PNGs before committing.
- Gallery scenes follow the same lint rules as `src/` (no hex colours, no ManimGL).
