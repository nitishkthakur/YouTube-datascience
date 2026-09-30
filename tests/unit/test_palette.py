import re

from dsanim import palette as P

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def test_all_colours_are_hex():
    for name in ["BG", "INK", "MUTED", "ACCENT_1", "ACCENT_2", "ACCENT_3", "DANGER"]:
        assert HEX.match(getattr(P, name)), name


def test_semantic_roles_map_to_raw_palette():
    # AGENTS.md §4: meaning is carried by colour consistently across the channel
    assert P.DATA == P.MUTED
    assert P.CONCEPT == P.ACCENT_1
    assert P.PARAM == P.ACCENT_2
    assert P.MODEL == P.ACCENT_3
    assert P.ERROR == P.DANGER
    assert P.TEXT == P.INK


def test_roles_are_distinct():
    roles = [P.DATA, P.DATA_FOCUS, P.CONCEPT, P.PARAM, P.MODEL, P.ERROR]
    assert len(set(roles)) == len(roles)


def test_type_sizes_meet_minimums_in_both_orientations():
    sizes = [P.SIZE_TITLE, P.SIZE_BODY, P.SIZE_LABEL, P.SIZE_EQUATION, P.SIZE_CAPTION]
    assert min(sizes) >= P.MIN_SIZE_LANDSCAPE
    assert min(sizes) * P.VERTICAL_TEXT_SCALE >= P.MIN_SIZE_VERTICAL


def test_fonts_are_the_open_licence_set():
    assert {P.FONT_TEXT, P.FONT_CODE, P.FONT_MATH} == {"Inter", "JetBrains Mono", "STIX Two Math"}


def test_motion_defaults_match_agents_md():
    assert P.RUN_TIME == 1.0 and P.ENTRANCE_TIME == 0.8
    assert 4.0 <= P.SWEEP_TIME <= 6.0
    assert P.TAIL_SILENCE >= 0.5
