from __future__ import annotations

from models import (
    Card,
    ColorGroup,
    ComparisonResult,
    EvaluationResult,
    HigherLowerGuess,
    InOutGuess,
    PositionResult,
    Suit,
)


def compare_cards(card1: Card, card2: Card) -> ComparisonResult:
    if card2.value > card1.value:
        return ComparisonResult.HIGHER
    if card2.value < card1.value:
        return ComparisonResult.LOWER
    return ComparisonResult.EQUAL


def locate_card_against_bounds(card1: Card, card2: Card, card3: Card) -> tuple[PositionResult, int, int]:
    low = min(card1.value, card2.value)
    high = max(card1.value, card2.value)

    # "Inside" is inclusive of both bounds.
    if low <= card3.value <= high:
        return PositionResult.INSIDE, low, high
    return PositionResult.OUTSIDE, low, high


def evaluate_step1(guess: ColorGroup, card1: Card) -> EvaluationResult:
    actual = card1.color_group
    success = guess == actual
    return EvaluationResult(
        step=1,
        success=success,
        expected=guess.value,
        actual=actual.value,
        details={
            "card1": str(card1),
            "card1_color": actual.value,
        },
    )


def evaluate_step2(guess: HigherLowerGuess, card1: Card, card2: Card) -> EvaluationResult:
    comparison = compare_cards(card1, card2)

    # Equal is neither higher nor lower -> always a loss.
    success = (
        (guess == HigherLowerGuess.HIGHER and comparison == ComparisonResult.HIGHER)
        or (guess == HigherLowerGuess.LOWER and comparison == ComparisonResult.LOWER)
    )

    return EvaluationResult(
        step=2,
        success=success,
        expected=guess.value,
        actual=comparison.value,
        details={
            "card1": str(card1),
            "card2": str(card2),
            "value1": card1.value,
            "value2": card2.value,
        },
    )


def evaluate_step3(guess: InOutGuess, card1: Card, card2: Card, card3: Card) -> EvaluationResult:
    position, low, high = locate_card_against_bounds(card1, card2, card3)

    success = (
        (guess == InOutGuess.INSIDE and position == PositionResult.INSIDE)
        or (guess == InOutGuess.OUTSIDE and position == PositionResult.OUTSIDE)
    )

    return EvaluationResult(
        step=3,
        success=success,
        expected=guess.value,
        actual=position.value,
        details={
            "card1": str(card1),
            "card2": str(card2),
            "card3": str(card3),
            "value1": card1.value,
            "value2": card2.value,
            "value3": card3.value,
            "lower_bound": low,
            "upper_bound": high,
            "inside_is_inclusive": True,
            "equal_first_two_cards": card1.value == card2.value,
        },
    )


def evaluate_step4(guess: Suit, card4: Card) -> EvaluationResult:
    actual = card4.suit
    success = guess == actual
    return EvaluationResult(
        step=4,
        success=success,
        expected=guess.value,
        actual=actual.value,
        details={
            "card4": str(card4),
        },
    )
