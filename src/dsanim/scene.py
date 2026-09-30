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

from manim import PMobject, Scene, VMobject, config
from manim.mobject.types.image_mobject import AbstractImageMobject

from dsanim import layout, narration, palette as P, typography
from dsanim.script import Script, parse

layout.apply_orientation()
config.background_color = P.BG
config.tex_template = typography.tex_template()


class NarrationOverrun(RuntimeError):
    pass


class SafeAreaViolation(RuntimeError):
    pass


def _visible(mobject) -> bool:
    """True if any part of the mobject would actually paint pixels.

    Only VMobjects, PMobjects and images are drawn; plain Mobjects such as ValueTracker
    carry points (the tracked value) but are never rendered.
    """
    for m in mobject.family_members_with_points():
        if isinstance(m, (AbstractImageMobject, PMobject)):
            return True
        if isinstance(m, VMobject) and (
                m.get_fill_opacity() > 0 or (m.get_stroke_opacity() > 0 and m.get_stroke_width() > 0)):
            return True
    return False


class BeatTracker:
    """Handle yielded by DSScene.beat(): timing information for the current beat."""

    def __init__(self, scene: "DSScene", audio: narration.BeatAudio, extend: float = 0.0):
        self.scene, self.audio, self.extend = scene, audio, extend
        self.start = scene.renderer.time

    @property
    def duration(self) -> float:
        """Seconds of narration in this beat."""
        return self.audio.duration

    @property
    def budget(self) -> float:
        """Seconds animations may use: narration plus the beat's silent `extend`."""
        return self.audio.duration + self.extend

    @property
    def elapsed(self) -> float:
        return self.scene.renderer.time - self.start

    @property
    def remaining(self) -> float:
        """Seconds of animation budget left in this beat (narration + extend)."""
        return max(self.budget - self.elapsed, 0.0)

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

    def safe_area_violations(self) -> list[str]:
        """Visible top-level mobjects whose bounding box leaves the safe area (AGENTS.md §4)."""
        out = []
        for m in self.mobjects:
            if _visible(m) and not self.layout.safe.contains(m, tol=1e-3):
                (x0, y0, _), (x1, y1, _) = m.get_corner([-1, -1, 0]), m.get_corner([1, 1, 0])
                out.append(f"{type(m).__name__} spans x[{x0:.2f},{x1:.2f}] y[{y0:.2f},{y1:.2f}]")
        return out

    def _check_safe_area(self, where: str) -> None:
        bad = self.safe_area_violations()
        if not bad:
            return
        msg = f"{where}: outside safe area {self.layout.safe}: " + "; ".join(bad)
        if os.environ.get("DSANIM_FINAL") == "1":
            raise SafeAreaViolation(msg)
        warnings.warn(msg)

    def eq(self, eq_id: str, **kw):
        """The equation `eq_id`, exactly as frozen in script.md."""
        return typography.math(self.script.eq(eq_id).latex, **kw)

    # --- narration-timed beats ------------------------------------------------------------
    @contextmanager
    def beat(self, beat_id: str, extend: float = 0.0):
        """Play a beat's narration; animations inside must fit its budget.

        Budget = narration duration + `extend`, the seconds of *silent visual time* this beat
        may run past its speech (a sweep or hold after the line ends). `extend` is budgeted
        per beat in the shot list and approved by Nitish; it is 0 by default.

        On exit the scene holds the final state until max(narration end, animation end) +
        TAIL_SILENCE, so every beat ends on >= 0.5 s of stillness and silence. The end state is
        then checked against the safe area: a warning while iterating, an error in final renders. Animations
        longer than the budget raise NarrationOverrun: shorten the animation or ask for a
        larger `extend` — never speed up the audio (AGENTS.md §7).
        """
        if extend < 0:
            raise ValueError("extend must be >= 0")
        b = self.script.beat(beat_id)
        audio = narration.load(self.script, b)
        if audio.placeholder:
            self.used_placeholder = True
            if os.environ.get("DSANIM_FINAL") == "1":
                raise RuntimeError(f"beat {beat_id} uses PLACEHOLDER audio in a final render")
        if audio.path:
            self.add_sound(str(audio.path))
        tracker = BeatTracker(self, audio, extend)
        yield tracker
        over = tracker.elapsed - tracker.budget
        if over > 1e-3 and audio.path:
            raise NarrationOverrun(
                f"beat {beat_id}: animations run {over:.2f}s past the budget of "
                f"{audio.duration:.2f}s narration ({audio.kind}) + {extend:.2f}s extend"
            )
        rest = max(audio.duration, tracker.elapsed) + P.TAIL_SILENCE - tracker.elapsed
        if rest > 1 / config.frame_rate:
            self.wait(rest)
        self._check_safe_area(f"end of beat {beat_id}")
