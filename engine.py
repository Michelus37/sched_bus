from __future__ import annotations

from typing import Optional

from deck import draw_card, shuffled_deck
from models import (
    ColorGroup,
    EvaluationResult,
    HigherLowerGuess,
    InOutGuess,
    RoundContext,
    RoundState,
    Suit,
)
from rules import evaluate_step1, evaluate_step2, evaluate_step3, evaluate_step4
from strategy import Strategy


def require_state(ctx: RoundContext, expected: RoundState) -> None:
    if ctx.state != expected:
        raise RuntimeError(f"Invalid state: expected {expected.name}, got {ctx.state.name}")


def validate_not_finished(ctx: RoundContext) -> None:
    if ctx.is_finished:
        raise RuntimeError("Round already finished.")


class RoundEngine:
    def __init__(self, stake: int = 500) -> None:
        self.stake = stake

    def new_round(self, seed: Optional[int] = None, preset_deck: Optional[list] = None) -> RoundContext:
        deck = list(preset_deck) if preset_deck is not None else shuffled_deck(seed=seed)
        ctx = RoundContext(stake=self.stake, state=RoundState.ROUND_INIT, deck=deck)
        ctx.add_event("ROUND_STARTED", stake=self.stake, deck_size=len(deck), seed=seed)
        ctx.state = RoundState.AWAIT_GUESS_COLOR
        return ctx

    def submit_color_guess(self, ctx: RoundContext, guess: ColorGroup) -> None:
        validate_not_finished(ctx)
        require_state(ctx, RoundState.AWAIT_GUESS_COLOR)
        ctx.guess_color = guess
        ctx.add_event("GUESS_SUBMITTED", step=1, guess=guess.value)
        ctx.state = RoundState.DRAW_FIRST_CARD

    def resolve_step1(self, ctx: RoundContext) -> EvaluationResult:
        validate_not_finished(ctx)
        require_state(ctx, RoundState.DRAW_FIRST_CARD)
        if ctx.guess_color is None:
            raise RuntimeError("Step 1 guess missing.")

        card1 = draw_card(ctx)
        result = evaluate_step1(ctx.guess_color, card1)
        ctx.add_evaluation(result)

        if result.success:
            ctx.state = RoundState.AWAIT_GUESS_HIGHER_LOWER
        else:
            ctx.finish_as_lost("step1_failed")
        return result

    def submit_higher_lower_guess(self, ctx: RoundContext, guess: HigherLowerGuess) -> None:
        validate_not_finished(ctx)
        require_state(ctx, RoundState.AWAIT_GUESS_HIGHER_LOWER)
        ctx.guess_higher_lower = guess
        ctx.add_event("GUESS_SUBMITTED", step=2, guess=guess.value)
        ctx.state = RoundState.DRAW_SECOND_CARD

    def resolve_step2(self, ctx: RoundContext) -> EvaluationResult:
        validate_not_finished(ctx)
        require_state(ctx, RoundState.DRAW_SECOND_CARD)
        if ctx.guess_higher_lower is None:
            raise RuntimeError("Step 2 guess missing.")
        if ctx.card1 is None:
            raise RuntimeError("Card 1 missing before step 2 resolution.")

        card2 = draw_card(ctx)
        result = evaluate_step2(ctx.guess_higher_lower, ctx.card1, card2)
        ctx.add_evaluation(result)

        if result.success:
            ctx.state = RoundState.AWAIT_GUESS_INSIDE_OUTSIDE
        else:
            ctx.finish_as_lost("step2_failed")
        return result

    def submit_inside_outside_guess(self, ctx: RoundContext, guess: InOutGuess) -> None:
        validate_not_finished(ctx)
        require_state(ctx, RoundState.AWAIT_GUESS_INSIDE_OUTSIDE)
        ctx.guess_inside_outside = guess
        ctx.add_event("GUESS_SUBMITTED", step=3, guess=guess.value)
        ctx.state = RoundState.DRAW_THIRD_CARD

    def resolve_step3(self, ctx: RoundContext) -> EvaluationResult:
        validate_not_finished(ctx)
        require_state(ctx, RoundState.DRAW_THIRD_CARD)
        if ctx.guess_inside_outside is None:
            raise RuntimeError("Step 3 guess missing.")
        if ctx.card1 is None or ctx.card2 is None:
            raise RuntimeError("Card 1 and Card 2 must exist before step 3 resolution.")

        card3 = draw_card(ctx)
        result = evaluate_step3(ctx.guess_inside_outside, ctx.card1, ctx.card2, card3)
        ctx.add_evaluation(result)

        if result.success:
            ctx.state = RoundState.AWAIT_GUESS_SUIT
        else:
            ctx.finish_as_lost("step3_failed")
        return result

    def submit_suit_guess(self, ctx: RoundContext, guess: Suit) -> None:
        validate_not_finished(ctx)
        require_state(ctx, RoundState.AWAIT_GUESS_SUIT)
        ctx.guess_suit = guess
        ctx.add_event("GUESS_SUBMITTED", step=4, guess=guess.value)
        ctx.state = RoundState.DRAW_FOURTH_CARD

    def resolve_step4(self, ctx: RoundContext) -> EvaluationResult:
        validate_not_finished(ctx)
        require_state(ctx, RoundState.DRAW_FOURTH_CARD)
        if ctx.guess_suit is None:
            raise RuntimeError("Step 4 guess missing.")

        card4 = draw_card(ctx)
        result = evaluate_step4(ctx.guess_suit, card4)
        ctx.add_evaluation(result)

        if result.success:
            ctx.finish_as_won()
        else:
            ctx.finish_as_lost("step4_failed")
        return result

    def play_full_round(self, strategy: Strategy, seed: Optional[int] = None, preset_deck: Optional[list] = None) -> RoundContext:
        ctx = self.new_round(seed=seed, preset_deck=preset_deck)

        self.submit_color_guess(ctx, strategy.choose_color(ctx))
        self.resolve_step1(ctx)
        if ctx.is_finished:
            return ctx

        self.submit_higher_lower_guess(ctx, strategy.choose_higher_lower(ctx))
        self.resolve_step2(ctx)
        if ctx.is_finished:
            return ctx

        self.submit_inside_outside_guess(ctx, strategy.choose_inside_outside(ctx))
        self.resolve_step3(ctx)
        if ctx.is_finished:
            return ctx

        self.submit_suit_guess(ctx, strategy.choose_suit(ctx))
        self.resolve_step4(ctx)
        return ctx
