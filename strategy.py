from __future__ import annotations

import random
from collections import Counter
from typing import Optional, Protocol

from models import Card, ColorGroup, HigherLowerGuess, InOutGuess, RoundContext, Suit


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


class HeuristicStrategy:
    """Greedy probability-based strategy using only the remaining deck.

    It always selects the option with the highest immediate success chance based
    on ``ctx.deck`` and the already revealed cards in ``ctx.drawn_cards``.

    This keeps the strategy fast, deterministic and much stronger than random,
    while staying easy to understand and extend later.
    """

    _SUIT_ORDER = (Suit.SPADES, Suit.HEARTS, Suit.CLUBS, Suit.DIAMONDS)

    def _remaining_cards(self, ctx: RoundContext) -> list[Card]:
        return ctx.deck

    def choose_color(self, ctx: RoundContext) -> ColorGroup:
        remaining = self._remaining_cards(ctx)
        red = sum(1 for card in remaining if card.color_group == ColorGroup.RED)
        black = len(remaining) - red
        return ColorGroup.RED if red >= black else ColorGroup.BLACK

    def choose_higher_lower(self, ctx: RoundContext) -> HigherLowerGuess:
        if ctx.card1 is None:
            raise RuntimeError("Card 1 must be known before choosing higher/lower.")

        remaining = self._remaining_cards(ctx)
        higher = sum(1 for card in remaining if card.value > ctx.card1.value)
        lower = sum(1 for card in remaining if card.value < ctx.card1.value)

        return HigherLowerGuess.HIGHER if higher >= lower else HigherLowerGuess.LOWER

    def choose_inside_outside(self, ctx: RoundContext) -> InOutGuess:
        if ctx.card1 is None or ctx.card2 is None:
            raise RuntimeError("Card 1 and Card 2 must be known before choosing inside/outside.")

        remaining = self._remaining_cards(ctx)
        low = min(ctx.card1.value, ctx.card2.value)
        high = max(ctx.card1.value, ctx.card2.value)

        inside = sum(1 for card in remaining if low <= card.value <= high)
        outside = len(remaining) - inside

        return InOutGuess.INSIDE if inside >= outside else InOutGuess.OUTSIDE

    def choose_suit(self, ctx: RoundContext) -> Suit:
        remaining = self._remaining_cards(ctx)
        suit_counts = Counter(card.suit for card in remaining)
        return max(self._SUIT_ORDER, key=lambda suit: (suit_counts[suit], -self._SUIT_ORDER.index(suit)))
