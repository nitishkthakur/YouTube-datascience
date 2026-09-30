import json
import subprocess
import sys

import pytest

from conftest import ROOT, load_tool

lint = load_tool("lint_scenes")


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


def test_inline_latex_banned_in_topics_only():
    src = 'eq = MathTex(r"y = x")'
    assert codes("topics/030-x/L1/scenes/s.py", src)[0] == ["E3"]
    assert codes("src/dsanim/typography.py", src)[0] == []


def test_eq_by_id_is_fine():
    assert codes("topics/030-x/L1/scenes/s.py", 'eq = self.eq("cond")') == ([], [])


def test_manim_colour_constants_banned_in_topics():
    assert codes("topics/a/L1/scenes/s.py", "Dot(color=BLUE)")[0] == ["E4"]
    assert codes("topics/a/L1/scenes/s.py", "Dot(color=BLUE_E)")[0] == ["E4"]
    assert codes("topics/a/L1/scenes/s.py", "Dot(color=P.CONCEPT)")[0] == []


def test_fixed_waits_warn_in_topics():
    assert codes("topics/a/L1/scenes/s.py", "self.wait(2)")[1] == ["W1"]
    assert codes("topics/a/L1/scenes/s.py", "b.wait_until('x')")[1] == []


def test_hook_mode_blocks_with_exit_2(tmp_path):
    bad = ROOT / "gallery" / "_lint_probe_tmp.py"
    bad.write_text('c = "#123456"\n')
    try:
        payload = json.dumps({"tool_input": {"file_path": str(bad)}})
        r = subprocess.run([sys.executable, str(ROOT / "tools/lint_scenes.py"), "--hook"],
                           input=payload, capture_output=True, text=True)
        assert r.returncode == 2 and "E2" in r.stderr
    finally:
        bad.unlink()


def test_hook_mode_ignores_out_of_scope_files():
    payload = json.dumps({"tool_input": {"file_path": str(ROOT / "README.md")}})
    r = subprocess.run([sys.executable, str(ROOT / "tools/lint_scenes.py"), "--hook"],
                       input=payload, capture_output=True, text=True)
    assert r.returncode == 0


def test_repo_is_lint_clean():
    r = subprocess.run([sys.executable, str(ROOT / "tools/lint_scenes.py")],
                       stdin=subprocess.DEVNULL, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
