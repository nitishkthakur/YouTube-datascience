"""Ledger — live numeric readouts under an equation: `x = 1500 kg`, `μ(x) = 19.7`, `n = 45`.

Binds each row to a callable so a sweep updates the numbers every frame, which makes
"σ(x) shrinks" legible instead of implied, and lets thin data show itself (n falling to 8).
Symbols are rendered with typography.symbol (single symbols, AGENTS.md §9); values with
DecimalNumber, coloured by role like the objects they describe.
"""

from __future__ import annotations

from typing import Callable

from manim import DOWN, LEFT, RIGHT, DecimalNumber, MathTex, VGroup

from dsanim import palette as P, typography as T
from dsanim.layout import Region


class Ledger(VGroup):
    """rows: (symbol_name, getter, options). options: decimals (int), unit (str), color (role).

    Example:
        Ledger([("x", lambda: x.get_value(), {"decimals": 0, "unit": "kg", "color": P.PARAM}),
                ("mu(x)", fit_mean, {"decimals": 1, "color": P.MODEL})], region=L.equation_lower)
    """

    def __init__(self, rows: list[tuple[str, Callable[[], float], dict]], region: Region | None = None,
                 size: int = P.SIZE_LABEL, row_buff: float = 0.25):
        super().__init__()
        self._getters: list[tuple[DecimalNumber, Callable[[], float]]] = []
        for name, getter, opts in rows:
            color = opts.get("color", P.TEXT)
            label = T.symbol(name, size=size, color=color)
            eq = MathTex("=", font_size=T.scaled(size), color=P.MUTED)
            value = DecimalNumber(getter(), num_decimal_places=opts.get("decimals", 1),
                                  font_size=T.scaled(size), color=color)
            parts = [label, eq, value]
            if opts.get("unit"):
                parts.append(T.label(opts["unit"], color=P.MUTED))
            row = VGroup(*parts).arrange(RIGHT, buff=0.18)
            self._getters.append((value, getter))
            self.add(row)
        self.arrange(DOWN, buff=row_buff, aligned_edge=LEFT)
        if region is not None:
            region.fit(self, pad=0.1)

    def refresh(self) -> "Ledger":
        """Pull every value from its getter (call from an updater during sweeps)."""
        for number, getter in self._getters:
            number.set_value(getter())
        return self

    def live(self) -> "Ledger":
        """Refresh every frame, including during waits (a dt updater is time-based)."""
        self.add_updater(lambda m, dt: m.refresh())
        return self
