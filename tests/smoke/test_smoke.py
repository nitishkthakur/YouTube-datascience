"""Smoke: does the toolchain work at all? Run first when something looks broken."""

import importlib
import shutil
import subprocess
import sys

import pytest

from conftest import ROOT, TINYTEX, render_env, run_manim, video_duration

pytestmark = pytest.mark.smoke


@pytest.mark.parametrize("mod", ["dsanim.palette", "dsanim.layout", "dsanim.typography",
                                 "dsanim.script", "dsanim.narration", "dsanim.data", "dsanim.scene"])
def test_modules_import(mod):
    importlib.import_module(mod)


def test_manim_version_is_pinned_range():
    import manim
    major, minor = (int(x) for x in manim.__version__.split(".")[:2])
    assert (major, minor) >= (0, 20) and (major, minor) < (0, 22)


def test_system_tools_present():
    assert shutil.which("ffmpeg") and shutil.which("ffprobe")
    assert (TINYTEX / "xelatex").exists() or shutil.which("xelatex")


def test_fonts_visible_to_pango():
    import manimpango
    from dsanim import palette as P
    fonts = set(manimpango.list_fonts())
    for f in (P.FONT_TEXT, P.FONT_CODE, P.FONT_MATH, P.FONT_MATH_TEXT):
        assert f in fonts, f


@pytest.mark.parametrize("tool", ["render", "contact_sheet", "check_script", "fetch_data",
                                  "new_topic", "lint_scenes", "tts_placeholder"])
def test_tools_compile(tool):
    subprocess.run([sys.executable, "-m", "py_compile", str(ROOT / "tools" / f"{tool}.py")], check=True)


def test_check_script_on_gallery():
    r = subprocess.run([sys.executable, str(ROOT / "tools/check_script.py"), str(ROOT / "gallery")],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "1.2" in r.stdout


@pytest.mark.slow
def test_xelatex_equation_renders():
    from dsanim.scene import DSScene  # noqa: F401  (installs the tex template)
    from dsanim import typography as T
    eq = T.math(r"Y \mid X=x \sim \mathcal{N}(\mu(x), \sigma(x)^2)")
    assert eq.width > 0 and len(eq.submobjects) > 0


@pytest.mark.slow
@pytest.mark.parametrize("vertical", [False, True])
def test_gallery_renders_at_ql(tmp_path, vertical):
    env = render_env(DSANIM_AUDIO_DIR=tmp_path / "none", DSANIM_VERTICAL=int(vertical))
    r = run_manim(ROOT / "gallery/style_sheet.py", "StyleSheet", "smoke", tmp_path / "media", env)
    assert r.returncode == 0, r.stderr[-2000:]
    assert video_duration(next((tmp_path / "media").glob("videos/**/smoke.mp4"))) > 5
