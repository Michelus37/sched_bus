import pytest

from engine import RoundEngine
from models import ColorGroup, HigherLowerGuess, InOutGuess, Rank, RoundState, Suit, Card



def test_new_round_starts_in_await_guess_color() -> None:
    engine = RoundEngine()
    ctx = engine.new_round(seed=123)
    assert ctx.state == RoundState.AWAIT_GUESS_COLOR
    assert ctx.is_finished is False



def test_submit_in_wrong_state_raises() -> None:
    engine = RoundEngine()
    ctx = engine.new_round(seed=123)
    with pytest.raises(RuntimeError, match="Invalid state"):
        engine.submit_higher_lower_guess(ctx, HigherLowerGuess.HIGHER)



def test_cannot_play_after_round_finished() -> None:
    engine = RoundEngine()
    preset_deck = [
        Card(Rank.ACE, Suit.SPADES),
    ]
    ctx = engine.new_round(preset_deck=preset_deck)
    engine.submit_color_guess(ctx, ColorGroup.RED)
    engine.resolve_step1(ctx)

    assert ctx.is_finished is True
    assert ctx.state == RoundState.ROUND_LOST

    with pytest.raises(RuntimeError, match="Round already finished"):
        engine.submit_color_guess(ctx, ColorGroup.RED)



def test_resolve_step2_requires_card1() -> None:
    engine = RoundEngine()
    ctx = engine.new_round(seed=123)
    ctx.state = RoundState.DRAW_SECOND_CARD
    ctx.guess_higher_lower = HigherLowerGuess.HIGHER

    with pytest.raises(RuntimeError, match="Card 1 missing"):
        engine.resolve_step2(ctx)



def test_deck_empty_raises_on_draw() -> None:
    engine = RoundEngine()
    ctx = engine.new_round(preset_deck=[])
    engine.submit_color_guess(ctx, ColorGroup.RED)

    with pytest.raises(RuntimeError, match="Deck is empty"):
        engine.resolve_step1(ctx)



def test_full_round_can_be_won_with_preset_deck() -> None:
    engine = RoundEngine()
    # draw_card() uses list.pop(), so the last list entry is drawn first.
    # Draw order here becomes:
    #   1) FOUR of HEARTS  -> red
    #   2) SIX of CLUBS    -> higher than 4
    #   3) FIVE of DIAMONDS -> inside [4, 6]
    #   4) SEVEN of SPADES -> exact suit hit
    preset_deck = [
        Card(Rank.SEVEN, Suit.SPADES),
        Card(Rank.FIVE, Suit.DIAMONDS),
        Card(Rank.SIX, Suit.CLUBS),
        Card(Rank.FOUR, Suit.HEARTS),
    ]
    ctx = engine.new_round(preset_deck=preset_deck)

    engine.submit_color_guess(ctx, ColorGroup.RED)
    step1 = engine.resolve_step1(ctx)
    engine.submit_higher_lower_guess(ctx, HigherLowerGuess.HIGHER)
    step2 = engine.resolve_step2(ctx)
    engine.submit_inside_outside_guess(ctx, InOutGuess.INSIDE)
    step3 = engine.resolve_step3(ctx)
    engine.submit_suit_guess(ctx, Suit.SPADES)
    step4 = engine.resolve_step4(ctx)

    assert all(step.success for step in (step1, step2, step3, step4))
    assert ctx.is_finished is True
    assert ctx.is_won is True
    assert ctx.state == RoundState.ROUND_WON
