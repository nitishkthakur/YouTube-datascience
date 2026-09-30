import pytest
from manim import config

from dsanim import palette as P, typography as T


def test_tex_template_uses_xelatex_and_stix():
    t = T.tex_template()
    assert t.tex_compiler == "xelatex" and t.output_format == ".xdv"
    assert "STIX Two Math" in t.preamble and "unicode-math" in t.preamble


def test_text_uses_channel_font_and_colour():
    t = T.text("hello")
    assert t.font == P.FONT_TEXT
    # Text keeps colour on its glyph submobjects (the parent's .color attribute stays default)
    assert all(g.get_fill_color().to_hex().upper() == P.TEXT.upper() for g in t)


def test_vertical_scales_text(monkeypatch):
    monkeypatch.setenv("DSANIM_VERTICAL", "0")
    assert T.scaled(P.SIZE_LABEL) == P.SIZE_LABEL
    monkeypatch.setenv("DSANIM_VERTICAL", "1")
    assert T.scaled(P.SIZE_LABEL) == pytest.approx(P.SIZE_LABEL * P.VERTICAL_TEXT_SCALE)


def test_font_size_equals_px_x_height_at_1080p():
    """Regression for the measured mapping documented in palette.py."""
    x = T.text("x", size=40)
    px_per_unit = 1080 / config.frame_height
    assert x.height * px_per_unit == pytest.approx(40, rel=0.1)


def test_symbol_whitelist():
    assert T.symbol("mu").tex_string.strip() == r"\mu"
    with pytest.raises(KeyError):
        T.symbol(r"\int_0^1")
