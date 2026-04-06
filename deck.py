from __future__ import annotations

import random
from typing import Optional

from models import Card, RoundContext, Rank, Suit


def create_standard_deck() -> list[Card]:
    return [Card(rank=rank, suit=suit) for suit in Suit for rank in Rank]


def shuffled_deck(seed: Optional[int] = None) -> list[Card]:
    deck = create_standard_deck()
    rng = random.Random(seed)
    rng.shuffle(deck)
    return deck


def draw_card(ctx: RoundContext) -> Card:
    if not ctx.deck:
        raise RuntimeError("Deck is empty. Cannot draw more cards.")

    card = ctx.deck.pop()
    ctx.drawn_cards.append(card)
    ctx.add_event(
        "CARD_DRAWN",
        card=str(card),
        remaining_deck_size=len(ctx.deck),
        draw_index=len(ctx.drawn_cards),
    )
    return card
