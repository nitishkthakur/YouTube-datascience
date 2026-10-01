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

import hashlib
import inspect
import json
import math
import os
import textwrap
import warnings
from contextlib import contextmanager
from pathlib import Path

import numpy as np
from manim import MathTex, PMobject, Scene, Text, VGroup, VMobject, config
from manim.mobject.types.image_mobject import AbstractImageMobject

from dsanim import captions, layout, narration, palette as P, typography
from dsanim.script import Script, parse

layout.apply_orientation()
config.background_color = P.BG
config.tex_template = typography.tex_template()
# Manim's partial-movie cache is off for every render: a cached play skips the animation code,
# its updaters AND add_sound (narration silently dropped on re-renders), and advances time by
# the unquantised duration. Incremental re-renders happen per scene instead (render_all.py
# keeps scenes whose inputs are unchanged).
config.disable_caching = True


class NarrationOverrun(RuntimeError):
    pass


class SafeAreaViolation(RuntimeError):
    pass


class ScriptNotFrozen(RuntimeError):
    pass


class RecordingStale(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _label(m) -> str:
    src = getattr(m, "tex_string", None) or getattr(m, "original_text", None) or getattr(m, "text", "")
    return f"{type(m).__name__}({str(src)[:30]!r})"


def _overlaps(box_a, box_b, tol: float = 0.02) -> bool:
    (alo, ahi), (blo, bhi) = box_a, box_b
    return not (ahi[0] <= blo[0] + tol or bhi[0] <= alo[0] + tol
                or ahi[1] <= blo[1] + tol or bhi[1] <= alo[1] + tol)


def _paints(m) -> bool:
    """Would this single mobject put pixels on screen? (ValueTracker etc. never do.)"""
    if isinstance(m, (AbstractImageMobject, PMobject)):
        return True
    return isinstance(m, VMobject) and (
        m.get_fill_opacity() > 0 or (m.get_stroke_opacity() > 0 and m.get_stroke_width() > 0))


def _visible_bbox(mobject):
    """(lo, hi) corners over the family members that actually paint, padded by half the widest
    stroke (a thick line flush with the edge still crosses it), or None."""
    members = [m for m in mobject.family_members_with_points() if _paints(m)]
    if not members:
        return None
    allp = np.concatenate([m.points for m in members])
    units_per_px = config.frame_width / config.pixel_width
    stroke = max((m.get_stroke_width() for m in members if isinstance(m, VMobject)), default=0.0)
    pad = 0.5 * stroke * units_per_px * (config.pixel_height / 1080)   # stroke widths are ~px at 1080p
    return allp.min(axis=0) - pad, allp.max(axis=0) + pad


def _visible(mobject) -> bool:
    return _visible_bbox(mobject) is not None


def frames(t: float) -> float:
    """Round a duration UP to whole frames so cached and rendered plays agree on time."""
    fps = config.frame_rate
    return math.ceil(t * fps - 1e-6) / fps


class BeatTracker:
    """Handle yielded by DSScene.beat(): timing information for the current beat."""

    def __init__(self, scene: "DSScene", audio: narration.BeatAudio, extend: float = 0.0):
        self.scene, self.audio, self.extend = scene, audio, extend
        self.start = scene.renderer.time
        self.marks_hit: dict[str, float] = {}  # mark -> seconds into the beat it was honoured

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
        """Seconds from now until [[mark]] is spoken — use as a run_time (whole frames)."""
        dt = self.audio.mark_time(mark) - self.elapsed
        late = dt < minimum
        if late:
            warnings.warn(f"beat {self.audio.beat.id}: already {-dt:.2f}s past [[{mark}]]")
        dt = frames(max(dt, minimum))
        self.marks_hit[mark] = {"hit": self.elapsed + dt, "late": late}
        return dt

    def wait_until(self, mark: str) -> None:
        """Hold until [[mark]] is spoken. Warns if the mark has already passed."""
        dt = self.audio.mark_time(mark) - self.elapsed
        late = dt < -1 / config.frame_rate
        if dt > 1 / config.frame_rate:
            self.scene.wait(frames(dt))
        elif late:
            warnings.warn(f"beat {self.audio.beat.id}: wait_until([[{mark}]]) called {-dt:.2f}s late")
        self.marks_hit[mark] = {"hit": self.elapsed, "late": late}


class DSScene(Scene):
    """Base scene: layout regions, script access, audio-timed beats.

    Every render also writes a timings sidecar (media/timings/<output_file>.json) listing each
    beat's start/end seconds, narration, caption cards and audio hash — tools/assemble.py
    builds chapters, SRT subtitles and the publish manifest from it; tools/make_shorts.py cuts
    chunks with it.
    """

    #: Path to script.md. Default: nearest script.md above the scene file.
    script_path: str | None = None
    #: Burn the narration into the caption band of vertical renders (AGENTS.md §10).
    captions: bool = True

    def setup(self):
        self.vertical = layout.is_vertical()
        self.layout = layout.regions(self.vertical)
        self.script = self._load_script()
        self.used_placeholder = False
        self.beat_log: list[dict] = []
        self._watermark = None
        self.final = os.environ.get("DSANIM_FINAL") == "1"
        self.test_render = os.environ.get("DSANIM_ALLOW_PLACEHOLDER") == "1"
        if self.final and not self.test_render and not self.script.frozen:
            raise ScriptNotFrozen(
                f"{self.script.path} is not frozen (status: {self.script.meta.get('status', 'draft')}); "
                "final renders need `status: frozen` (AGENTS.md §5.1) — or --allow-placeholder for a test render")

    def tear_down(self):
        super().tear_down()
        self.write_timings()

    # --- timings sidecar ---------------------------------------------------------------------
    def timings_path(self) -> Path:
        name = config.output_file or type(self).__name__
        return Path(config.media_dir) / "timings" / f"{Path(str(name)).stem}.json"

    def write_timings(self) -> Path:
        path = self.timings_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "scene": type(self).__name__,
            "script": str(self.script.path),
            "script_status": self.script.meta.get("status", "draft"),
            "vertical": self.vertical,
            "frame_rate": config.frame_rate,
            "pixel_size": [config.pixel_width, config.pixel_height],
            "duration": float(self.renderer.time),
            "used_placeholder": self.used_placeholder,
            "beats": self.beat_log,
        }, indent=1))
        return path

    # --- placeholder guard ---------------------------------------------------------------------
    def _placeholder_in_final(self, beat_id: str) -> None:
        if not self.test_render:
            raise RuntimeError(
                f"beat {beat_id} uses PLACEHOLDER audio in a final render "
                "(render.py --allow-placeholder makes a watermarked test render instead)")
        if self._watermark is None:
            # lives in the bottom gutter, outside the safe area, so it never hides content
            frame, safe = layout.frame(), self.layout.safe
            wm = typography.label("PLACEHOLDER VOICE — NOT FOR PUBLICATION", color=P.ERROR)
            gutter = safe.bottom - frame.bottom
            wm.scale_to_fit_height(min(wm.height, 0.6 * gutter))
            if wm.width > 0.6 * safe.width:
                wm.scale_to_fit_width(0.6 * safe.width)
            wm.move_to([safe.right, frame.bottom + 0.2 * gutter, 0], aligned_edge=np.array([1.0, -1.0, 0.0]))
            self._watermark = wm
            self.add_foreground_mobject(wm)

    def _check_recording(self, beat) -> None:
        """A final render refuses a recording whose words changed since it was registered."""
        manifest = self.script.path.parent / "audio_manifest.json"
        if not manifest.exists():
            return
        entry = (json.loads(manifest.read_text()).get("beats") or {}).get(beat.key)
        if entry and entry.get("text_sha256") != hashlib.sha256(beat.text.encode()).hexdigest():
            raise RecordingStale(
                f"beat {beat.id}: the script's words changed after {entry['wav']} was recorded "
                "(tools/audio_manifest.py verify) — re-record or restore the words")

    # --- captions (vertical) -----------------------------------------------------------------
    def _caption_track(self, cards: list[captions.Caption], start_time: float) -> VGroup:
        """A VGroup in the caption band showing the card for the current time.

        All cards are built up front and only their opacity changes: Manim snapshots the
        moving mobjects when a play starts, so swapping children mid-play would leave the old
        card drawn from the snapshot (ghost captions). Structure never changes here.
        """
        region = self.layout.caption
        holder = VGroup(*[
            region.fit(typography.text("\n".join(textwrap.wrap(c.text, captions.LINE_CHARS)),
                                       size=P.SIZE_CAPTION), pad=0.1).set_opacity(0.0)
            for c in cards])
        holder.current = -1

        def update(m, dt):  # dt makes it a time-based updater: waits render every frame
            t = self.renderer.time - start_time
            idx = next((i for i, c in enumerate(cards) if c.start <= t < c.end), len(cards) - 1)
            if idx != m.current:
                if m.current >= 0:
                    m[m.current].set_opacity(0.0)
                m[idx].set_opacity(1.0)
                m.current = idx

        holder.add_updater(update)
        return holder

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
        """Visible top-level mobjects whose painted bounding box leaves the safe area (AGENTS.md §4)."""
        out = []
        for m in self.mobjects:
            if m is self._watermark:
                continue
            box = _visible_bbox(m)
            # tol ≈ 2.7 px at 1080p: a hairline drawn exactly on the safe border is not a violation
            if box is not None and not self.layout.safe.contains_box(*box, tol=0.02):
                (x0, y0, _), (x1, y1, _) = box
                out.append(f"{type(m).__name__} spans x[{x0:.2f},{x1:.2f}] y[{y0:.2f},{y1:.2f}]")
        return out

    def text_overlaps(self) -> list[str]:
        """Pairs of visible Text/MathTex whose bounding boxes overlap (AGENTS.md §8: no text over text)."""
        texts = []
        for top in self.mobjects:
            for m in top.get_family():
                if isinstance(m, (Text, MathTex)) and m is not self._watermark:
                    box = _visible_bbox(m)
                    if box is not None:
                        texts.append((m, box))
        out = []
        for i, (a, box_a) in enumerate(texts):
            for b, box_b in texts[i + 1:]:
                if b in a.get_family() or a in b.get_family():
                    continue
                if _overlaps(box_a, box_b):
                    out.append(f"{_label(a)} × {_label(b)}")
        return out

    def _check_safe_area(self, where: str) -> None:
        bad = self.safe_area_violations()
        if bad:
            msg = f"{where}: outside safe area {self.layout.safe}: " + "; ".join(bad)
            # an error in finals, and already at 720p review renders once the script is frozen —
            # so the problem surfaces before the long render, not after it (short side: a 9:16
            # render at -ql is 480x854)
            review_quality = min(config.pixel_width, config.pixel_height) >= 720
            if self.final or (self.script.frozen and review_quality):
                raise SafeAreaViolation(msg)
            warnings.warn(msg)
        overlaps = self.text_overlaps()
        if overlaps:
            warnings.warn(f"{where}: text overlapping text: " + "; ".join(overlaps))

    def eq(self, eq_id: str, terms: list[str] | None = None, roles: dict[str, str] | None = None, **kw):
        """The equation `eq_id`, exactly as frozen in script.md.

        terms tokenises it for term-wise reveal/morph; roles colours substrings by role
        (see typography.math). Neither changes the LaTeX — that is checked at runtime.
        """
        return typography.math(self.script.eq(eq_id).latex, terms=terms, roles=roles, **kw)

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
            if self.final:
                self._placeholder_in_final(beat_id)
        if audio.path is None and self.final and not self.test_render:
            raise RuntimeError(f"beat {beat_id} has no narration at all (neither recorded nor placeholder) "
                               "— a final render needs a recording")
        if audio.word_times is not None and not audio.aligned:
            warnings.warn(f"beat {beat_id}: {len(audio.word_times)} word timings for {len(b.words)} words — "
                          "marks and captions fall back to interpolation")
        if audio.path:
            if self.final and not self.test_render and not audio.placeholder:
                self._check_recording(b)
            self.add_sound(str(audio.path))
        tracker = BeatTracker(self, audio, extend)
        cards = captions.captions_for(b.words, audio.duration, audio.word_times)
        track = None
        if self.vertical and self.captions and self.layout.caption is not None and cards:
            track = self._caption_track(cards, tracker.start)
            self.add(track)
        yield tracker
        over = tracker.elapsed - tracker.budget
        if over > 1e-3:
            msg = (f"beat {beat_id}: animations run {over:.2f}s past the budget of "
                   f"{audio.duration:.2f}s narration ({audio.kind}) + {extend:.2f}s extend")
            if audio.path:
                raise NarrationOverrun(msg)
            warnings.warn(msg + " — estimate only; real audio may differ")
        rest = max(audio.duration, tracker.elapsed) + P.TAIL_SILENCE - tracker.elapsed
        if rest > 1 / config.frame_rate:
            self.wait(frames(rest))
        if track is not None:
            self.remove(track)
        self.beat_log.append({
            "id": b.id, "key": b.key, "start": tracker.start,
            "speech_end": tracker.start + audio.duration, "end": float(self.renderer.time),
            "extend": extend, "audio": audio.kind, "aligned": audio.aligned,
            "audio_file": str(audio.path) if audio.path else None,
            "audio_sha256": _sha256(audio.path) if audio.path else None,
            "text": b.text,
            "marks": {name: {"planned": audio.mark_time(name), **info}
                      for name, info in tracker.marks_hit.items()},
            "captions": [{"text": c.text, "start": c.start, "end": c.end} for c in cards],
        })
        self._check_safe_area(f"end of beat {beat_id}")
