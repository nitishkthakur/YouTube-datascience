"""DSScene — the base class every topic scene inherits.

Importing this module configures Manim for the channel (orientation, background, XeLaTeX
math template), so it must be imported before any Scene is constructed — which is always
true for `from dsanim.scene import DSScene` at the top of a scene file.

Usage in a topic scene (topics/<concept>/<tier>/scenes/s03_conditional.py):

    from manim import *
    from dsanim.scene import DSScene
    from dsanim import palette as P

    class Scene03(DSScene):
        def construct(self):
            # --- Beat 3.1 -------------------------------------------------------
            with self.beat("3.1") as b:
                eq = self.eq("marginal")                    # LaTeX from script.md
                self.play(Write(eq), run_time=b.until("collapse"))
                ...
"""

from __future__ import annotations

import inspect
import os
import warnings
from contextlib import contextmanager
from pathlib import Path

from manim import Scene, config

from dsanim import layout, narration, palette as P, typography
from dsanim.script import Script, parse

layout.apply_orientation()
config.background_color = P.BG
config.tex_template = typography.tex_template()


class NarrationOverrun(RuntimeError):
    pass


class BeatTracker:
    """Handle yielded by DSScene.beat(): timing information for the current beat."""

    def __init__(self, scene: "DSScene", audio: narration.BeatAudio):
        self.scene, self.audio = scene, audio
        self.start = scene.renderer.time

    @property
    def duration(self) -> float:
        return self.audio.duration

    @property
    def elapsed(self) -> float:
        return self.scene.renderer.time - self.start

    @property
    def remaining(self) -> float:
        """Seconds of narration left in this beat."""
        return max(self.duration - self.elapsed, 0.0)

    def until(self, mark: str, minimum: float = 0.1) -> float:
        """Seconds from now until [[mark]] is spoken — use as a run_time or wait."""
        dt = self.audio.mark_time(mark) - self.elapsed
        if dt < minimum:
            warnings.warn(f"beat {self.audio.beat.id}: already {-dt:.2f}s past [[{mark}]]")
        return max(dt, minimum)

    def wait_until(self, mark: str) -> None:
        dt = self.audio.mark_time(mark) - self.elapsed
        if dt > 1 / config.frame_rate:
            self.scene.wait(dt)


class DSScene(Scene):
    """Base scene: layout regions, script access, audio-timed beats."""

    #: Path to script.md. Default: nearest script.md above the scene file.
    script_path: str | None = None

    def setup(self):
        self.vertical = layout.is_vertical()
        self.layout = layout.regions(self.vertical)
        self.script = self._load_script()
        self.used_placeholder = False

    # --- script access ----------------------------------------------------------------
    def _load_script(self) -> Script:
        here = Path(inspect.getfile(type(self))).resolve().parent
        if self.script_path:
            return parse(here / self.script_path)
        for parent in [here, *here.parents]:
            if (parent / "script.md").exists():
                return parse(parent / "script.md")
            if (parent / "pyproject.toml").exists():
                break
        raise FileNotFoundError(f"no script.md above {here}")

    def eq(self, eq_id: str, **kw):
        """The equation `eq_id`, exactly as frozen in script.md."""
        return typography.math(self.script.eq(eq_id).latex, **kw)

    # --- narration-timed beats ------------------------------------------------------------
    @contextmanager
    def beat(self, beat_id: str):
        """Play a beat's narration; animations inside must finish before it ends.

        On exit the scene waits out the rest of the narration plus TAIL_SILENCE, so every
        beat ends on >= 0.5 s of silence with the final state held on screen. If the
        animations ran longer than the narration, NarrationOverrun is raised: shorten the
        animation, never speed up the audio (AGENTS.md §7).
        """
        b = self.script.beat(beat_id)
        audio = narration.load(self.script, b)
        if audio.placeholder:
            self.used_placeholder = True
            if os.environ.get("DSANIM_FINAL") == "1":
                raise RuntimeError(f"beat {beat_id} uses PLACEHOLDER audio in a final render")
        if audio.path:
            self.add_sound(str(audio.path))
        tracker = BeatTracker(self, audio)
        yield tracker
        over = tracker.elapsed - audio.duration
        if over > 1e-3 and audio.path:
            raise NarrationOverrun(
                f"beat {beat_id}: animations run {over:.2f}s past narration "
                f"({audio.duration:.2f}s, {audio.kind})"
            )
        rest = audio.duration + P.TAIL_SILENCE - tracker.elapsed
        if rest > 1 / config.frame_rate:
            self.wait(rest)
