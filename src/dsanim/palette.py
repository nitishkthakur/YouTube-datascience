"""Colours, fonts and type sizes — the single source of truth for the channel's look.

Nothing else in the repo may contain a colour literal or a font name. Nitish owns these
values; change them here and nowhere else (every past topic re-renders with the change,
which is why published topics are tagged — see AGENTS.md §3).
"""

# --- Raw palette -------------------------------------------------------------------------
BG = "#0F1115"        # near-black, slightly warm
INK = "#E8E6E1"       # primary text
MUTED = "#6B7280"     # de-emphasised data
ACCENT_1 = "#2DD4BF"  # teal
ACCENT_2 = "#F59E0B"  # amber
ACCENT_3 = "#A78BFA"  # violet
DANGER = "#F87171"    # coral

# --- Semantic roles (use THESE in scenes; the meaning is channel-wide) --------------------
DATA = MUTED          # raw observations at rest
DATA_FOCUS = INK      # observations currently selected / in the band
CONCEPT = ACCENT_1    # the thing we are talking about
PARAM = ACCENT_2      # the second thing / the parameter / the conditioning value
MODEL = ACCENT_3      # the model / the estimate
ERROR = DANGER        # errors, residuals, what breaks
TEXT = INK

FADED_OPACITY = 0.35  # de-emphasised data: still reads as a cloud being sliced (20% vanished)

# --- Fonts (open licence only: Inter OFL, JetBrains Mono OFL, STIX Two OFL) ---------------
FONT_TEXT = "Inter"
FONT_CODE = "JetBrains Mono"
FONT_MATH = "STIX Two Math"
FONT_MATH_TEXT = "STIX Two Text"  # \text{...} inside equations

# --- Type sizes (Manim font_size units) ----------------------------------------------------
# Measured (Manim 0.21, Inter): font_size N renders with an x-height of ~N px and a cap
# height of ~1.36*N px at 1080p, in both orientations (1 unit = 135 px; see layout.py).
# So "N px-equivalent" in AGENTS.md == font_size N. Minimums are enforced by tests.
SIZE_TITLE = 56
SIZE_BODY = 40
SIZE_LABEL = 32
SIZE_TICK = 28        # axis tick numbers: the smallest, quietest text on screen
SIZE_EQUATION = 44
SIZE_CAPTION = 36

MIN_SIZE_LANDSCAPE = 28  # AGENTS.md §4: ≥ 28 px-equivalent at 1080p
MIN_SIZE_VERTICAL = 40   # AGENTS.md §10: ≥ 40 px-equivalent in Shorts
VERTICAL_TEXT_SCALE = 1.25  # typography.* multiplies every size by this in vertical renders

# --- Motion defaults (seconds) -------------------------------------------------------------
RUN_TIME = 1.0
ENTRANCE_TIME = 0.8
SWEEP_TIME = 5.0
TAIL_SILENCE = 0.5       # minimum silence after a beat's animations (AGENTS.md §7)
