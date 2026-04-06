from __future__ import annotations

import random
from typing import Optional, Protocol

from models import ColorGroup, HigherLowerGuess, InOutGuess, RoundContext, Suit


class Strategy(Protocol):
    def choose_color(self, ctx: RoundContext) -> ColorGroup: ...
    def choose_higher_lower(self, ctx: RoundContext) -> HigherLowerGuess: ...
    def choose_inside_outside(self, ctx: RoundContext) -> InOutGuess: ...
    def choose_suit(self, ctx: RoundContext) -> Suit: ...


class RandomStrategy:
    """Simple placeholder strategy for testing and simulation."""

    def __init__(self, seed: Optional[int] = None) -> None:
        self.rng = random.Random(seed)

    def choose_color(self, ctx: RoundContext) -> ColorGroup:
        return self.rng.choice(list(ColorGroup))

    def choose_higher_lower(self, ctx: RoundContext) -> HigherLowerGuess:
        return self.rng.choice(list(HigherLowerGuess))

    def choose_inside_outside(self, ctx: RoundContext) -> InOutGuess:
        return self.rng.choice(list(InOutGuess))

    def choose_suit(self, ctx: RoundContext) -> Suit:
        return self.rng.choice(list(Suit))
