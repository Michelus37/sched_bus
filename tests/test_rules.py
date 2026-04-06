import pytest

from models import Card, ColorGroup, HigherLowerGuess, InOutGuess, Rank, Suit
from rules import evaluate_step1, evaluate_step2, evaluate_step3, evaluate_step4, locate_card_against_bounds


def test_step1_color_match_success() -> None:
    result = evaluate_step1(ColorGroup.RED, Card(Rank.ACE, Suit.HEARTS))
    assert result.success is True
    assert result.actual == "rot"


def test_step1_color_match_failure() -> None:
    result = evaluate_step1(ColorGroup.BLACK, Card(Rank.ACE, Suit.HEARTS))
    assert result.success is False


def test_step2_equal_is_always_loss_for_higher() -> None:
    result = evaluate_step2(
        HigherLowerGuess.HIGHER,
        Card(Rank.TEN, Suit.HEARTS),
        Card(Rank.TEN, Suit.SPADES),
    )
    assert result.success is False
    assert result.actual == "equal"


def test_step2_equal_is_always_loss_for_lower() -> None:
    result = evaluate_step2(
        HigherLowerGuess.LOWER,
        Card(Rank.FIVE, Suit.HEARTS),
        Card(Rank.FIVE, Suit.CLUBS),
    )
    assert result.success is False
    assert result.actual == "equal"


@pytest.mark.parametrize(
    ("guess", "card1", "card2", "card3", "expected_success"),
    [
        (InOutGuess.INSIDE, Card(Rank.FIVE, Suit.HEARTS), Card(Rank.JACK, Suit.SPADES), Card(Rank.FIVE, Suit.CLUBS), True),
        (InOutGuess.INSIDE, Card(Rank.FIVE, Suit.HEARTS), Card(Rank.JACK, Suit.SPADES), Card(Rank.JACK, Suit.CLUBS), True),
        (InOutGuess.OUTSIDE, Card(Rank.FIVE, Suit.HEARTS), Card(Rank.JACK, Suit.SPADES), Card(Rank.JACK, Suit.CLUBS), False),
    ],
)
def test_step3_inside_is_inclusive(guess, card1, card2, card3, expected_success) -> None:
    result = evaluate_step3(guess, card1, card2, card3)
    assert result.success is expected_success
    assert result.details["inside_is_inclusive"] is True


def test_step3_uses_min_max_independent_of_card_order() -> None:
    card1 = Card(Rank.QUEEN, Suit.HEARTS)
    card2 = Card(Rank.FOUR, Suit.SPADES)
    card3 = Card(Rank.SEVEN, Suit.CLUBS)

    position, low, high = locate_card_against_bounds(card1, card2, card3)

    assert position.value == "inside"
    assert low == 4
    assert high == 12


def test_step3_equal_first_two_cards_only_same_value_is_inside() -> None:
    same_value_result = evaluate_step3(
        InOutGuess.INSIDE,
        Card(Rank.EIGHT, Suit.HEARTS),
        Card(Rank.EIGHT, Suit.SPADES),
        Card(Rank.EIGHT, Suit.CLUBS),
    )
    other_value_result = evaluate_step3(
        InOutGuess.INSIDE,
        Card(Rank.EIGHT, Suit.HEARTS),
        Card(Rank.EIGHT, Suit.SPADES),
        Card(Rank.NINE, Suit.CLUBS),
    )

    assert same_value_result.success is True
    assert same_value_result.details["equal_first_two_cards"] is True
    assert other_value_result.success is False


def test_step4_exact_suit_match_only() -> None:
    hit = evaluate_step4(Suit.DIAMONDS, Card(Rank.KING, Suit.DIAMONDS))
    miss = evaluate_step4(Suit.DIAMONDS, Card(Rank.KING, Suit.HEARTS))

    assert hit.success is True
    assert miss.success is False
