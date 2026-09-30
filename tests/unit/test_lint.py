import io
import json
import subprocess
import sys

import pytest

from conftest import ROOT, load_tool

lint = load_tool("lint_scenes")
TOPIC = "topics/030-x/L1/scenes/s03.py"


def codes(rel, src):
    errors, warnings = lint.lint_source(rel, src)
    return sorted({e.split(": ")[1].split()[0] for e in errors}), \
        sorted({w.split(": ")[1].split()[0] for w in warnings})


@pytest.mark.parametrize("src", [
    "from manimlib import *", "self.play(ShowCreation(c))", "TextMobject('x')",
    "TexMobject('x')", "class S(Scene):\n    CONFIG = {'a': 1}\n",
])
def test_manimgl_isms_are_errors_everywhere(src):
    assert codes("src/dsanim/x.py", src)[0] == ["E1"]


def test_hex_colours_only_allowed_in_palette():
    assert codes("gallery/x.py", 'c = "#FF0000"')[0] == ["E2"]
    assert codes("src/dsanim/palette.py", 'BG = "#0F1115"')[0] == []


@pytest.mark.parametrize("src", [
    'eq = MathTex(r"y = x")', "eq = MathTex(latex_var)", 'MathTex(f"{a}")', 'Tex("hi")',
    'T.math(r"\\mu")', 'typography.math(s)',
])
def test_inline_equations_banned_in_topics(src):
    assert codes(TOPIC, src)[0] == ["E3"]
    assert codes("src/dsanim/typography.py", src)[0] == []


def test_eq_by_id_and_symbol_are_fine():
    assert codes(TOPIC, 'eq = self.eq("cond")\ns = T.symbol("mu")') == ([], [])


@pytest.mark.parametrize("src", ["Dot(color=BLUE)", "Dot(BLUE_E)", "d.set_color(RED)", "c = TEAL"])
def test_manim_colour_constants_banned_in_topics(src):
    assert codes(TOPIC, src)[0] == ["E4"]


def test_role_colours_are_fine():
    assert codes(TOPIC, "Dot(color=P.CONCEPT).set_color(P.MODEL)")[0] == []


@pytest.mark.parametrize("src", ["self.wait(2)", "self.wait(HOLD)"])
def test_fixed_waits_warn_in_topics(src):
    assert codes(TOPIC, src)[1] == ["W1"]


def test_tracker_driven_waits_do_not_warn():
    assert codes(TOPIC, 'b.wait_until("x")\nself.wait(b.remaining)\nself.wait(frames(0.5))')[1] == []


def test_syntax_error_is_reported():
    assert codes(TOPIC, "def (:")[0] == ["E0"]


def test_hook_mode_blocks_with_exit_2(tmp_path):
    bad = tmp_path / "gallery" / "probe.py"
    bad.parent.mkdir()
    bad.write_text('c = "#123456"\n')
    payload = io.StringIO(json.dumps({"tool_input": {"file_path": str(bad)}}))
    assert lint.main(["--hook"], root=tmp_path, stdin=payload) == 2


def test_hook_mode_ignores_out_of_scope_files(tmp_path):
    (tmp_path / "README.md").write_text('"#123456"')
    payload = io.StringIO(json.dumps({"tool_input": {"file_path": str(tmp_path / "README.md")}}))
    assert lint.main(["--hook"], root=tmp_path, stdin=payload) == 0


def test_repo_is_lint_clean():
    r = subprocess.run([sys.executable, str(ROOT / "tools/lint_scenes.py")],
                       stdin=subprocess.DEVNULL, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
