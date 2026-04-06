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


class LookaheadStrategy(HeuristicStrategy):
    """Stronger strategy with limited forward lookahead.

    Differences to ``HeuristicStrategy``:
    - step 2 is not chosen only by immediate hit chance
    - step 3 also values how good the remaining suit distribution becomes

    This stays practical for simulation while usually outperforming the plain
    greedy heuristic.
    """

    def choose_higher_lower(self, ctx: RoundContext) -> HigherLowerGuess:
        if ctx.card1 is None:
            raise RuntimeError("Card 1 must be known before choosing higher/lower.")

        remaining = list(ctx.deck)
        scores = {
            guess: self._expected_round_win_after_hl_guess(ctx.card1.value, remaining, guess)
            for guess in HigherLowerGuess
        }
        return max(HigherLowerGuess, key=lambda guess: scores[guess])

    def choose_inside_outside(self, ctx: RoundContext) -> InOutGuess:
        if ctx.card1 is None or ctx.card2 is None:
            raise RuntimeError("Card 1 and Card 2 must be known before choosing inside/outside.")

        remaining = list(ctx.deck)
        scores = {
            guess: self._expected_round_win_after_io_guess(ctx.card1.value, ctx.card2.value, remaining, guess)
            for guess in InOutGuess
        }
        return max(InOutGuess, key=lambda guess: scores[guess])

    def _expected_round_win_after_hl_guess(
        self,
        card1_value: int,
        remaining: list[Card],
        guess: HigherLowerGuess,
    ) -> float:
        if not remaining:
            return 0.0

        total = 0.0
        total_count = len(remaining)
        for idx, card2 in enumerate(remaining):
            success = (
                (guess == HigherLowerGuess.HIGHER and card2.value > card1_value)
                or (guess == HigherLowerGuess.LOWER and card2.value < card1_value)
            )
            if not success:
                continue

            next_remaining = remaining[:idx] + remaining[idx + 1 :]
            total += self._best_expected_round_win_after_step2(card1_value, card2.value, next_remaining)

        return total / total_count

    def _best_expected_round_win_after_step2(
        self,
        card1_value: int,
        card2_value: int,
        remaining: list[Card],
    ) -> float:
        return max(
            self._expected_round_win_after_io_guess(card1_value, card2_value, remaining, guess)
            for guess in InOutGuess
        )

    def _expected_round_win_after_io_guess(
        self,
        card1_value: int,
        card2_value: int,
        remaining: list[Card],
        guess: InOutGuess,
    ) -> float:
        if not remaining:
            return 0.0

        low = min(card1_value, card2_value)
        high = max(card1_value, card2_value)
        total = 0.0
        total_count = len(remaining)

        for idx, card3 in enumerate(remaining):
            is_inside = low <= card3.value <= high
            success = (
                (guess == InOutGuess.INSIDE and is_inside)
                or (guess == InOutGuess.OUTSIDE and not is_inside)
            )
            if not success:
                continue

            next_remaining = remaining[:idx] + remaining[idx + 1 :]
            total += self._best_suit_hit_probability(next_remaining)

        return total / total_count

    def _best_suit_hit_probability(self, remaining: list[Card]) -> float:
        if not remaining:
            return 0.0
        suit_counts = Counter(card.suit for card in remaining)
        best = max(suit_counts.values(), default=0)
        return best / len(remaining)
