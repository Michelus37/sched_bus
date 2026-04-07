from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from deck import create_standard_deck
from detector import LiveUIState
from game_reader import GameReader, LiveGameSnapshot
from models import Card, RoundContext
from strategy import Strategy


class AdapterActionType(Enum):
    WAIT = auto()
    CLICK_READY = auto()
    CHOOSE_COLOR = auto()
    CHOOSE_HIGHER_LOWER = auto()
    CHOOSE_INSIDE_OUTSIDE = auto()
    CHOOSE_SUIT = auto()


@dataclass(slots=True)
class AdapterAction:
    type: AdapterActionType
    payload: dict | None = None


CARD_DETECT_MAX_RETRIES = 6  # polls before giving up on card detection and deciding anyway


class LiveAdapter:
    """Bridges live UI state to strategy decisions.

    Maintains a RoundContext approximation for the strategy:
    - deck starts as a full shuffled 52-card deck (approximation)
    - detected cards are injected into drawn_cards and removed from deck
    - the strategy uses this context to compute probabilities

    If a card can't be detected after CARD_DETECT_MAX_RETRIES polls, the
    strategy decides anyway based on remaining deck probabilities alone.

    State tracking prevents double-clicking within the same UI state.
    """

    def __init__(self, reader: GameReader, strategy: Strategy) -> None:
        self.reader = reader
        self.strategy = strategy
        self._ctx: Optional[RoundContext] = None
        self._last_state: LiveUIState = LiveUIState.UNKNOWN
        self._state_handled: bool = False  # True once we've acted on the current state
        self._card_wait_ticks: int = 0     # how many ticks we've waited for card detection

    def tick(self) -> tuple[LiveGameSnapshot, AdapterAction]:
        snapshot = self.reader.read_snapshot()
        current_state = snapshot.ui_state

        if current_state != self._last_state:
            self._state_handled = False
            self._card_wait_ticks = 0
            self._on_state_change(current_state)
            self._last_state = current_state

        action = self._decide(current_state, snapshot)

        if action.type != AdapterActionType.WAIT:
            self._state_handled = True

        return snapshot, action

    # ── Internal ──────────────────────────────────────────────────────────────

    def _on_state_change(self, new: LiveUIState) -> None:
        if new == LiveUIState.WAIT_READY:
            self._reset_ctx()

    def _reset_ctx(self) -> None:
        deck = create_standard_deck()
        random.shuffle(deck)
        self._ctx = RoundContext(deck=deck)

    def _ensure_ctx(self) -> RoundContext:
        if self._ctx is None:
            self._reset_ctx()
        return self._ctx  # type: ignore[return-value]

    def _try_inject_cards_up_to(self, snapshot: LiveGameSnapshot, slot: int) -> bool:
        """Inject all cards from slot 0 up to and including `slot`.

        The game reveals cards one by one:
          slot 0 → visible after color decision   (1 card on table)
          slot 1 → visible after H/L decision     (2 cards on table)
          slot 2 → visible after I/O decision     (3 cards on table)

        Returns True only when the card at `slot` is available in ctx.
        """
        ctx = self._ensure_ctx()

        for s in range(slot + 1):
            if len(ctx.drawn_cards) > s:
                continue  # already injected

            if len(snapshot.visible_cards) <= s:
                return False  # card not detected on screen yet

            card: Card = snapshot.visible_cards[s]
            ctx.drawn_cards.append(card)

            # Keep deck approximation in sync
            for i, c in enumerate(ctx.deck):
                if c == card:
                    ctx.deck.pop(i)
                    break

        return True

    def _decide(self, state: LiveUIState, snapshot: LiveGameSnapshot) -> AdapterAction:
        if self._state_handled:
            return AdapterAction(AdapterActionType.WAIT)

        if state == LiveUIState.WAIT_READY:
            return AdapterAction(AdapterActionType.CLICK_READY)

        ctx = self._ensure_ctx()

        if state == LiveUIState.WAIT_COLOR_DECISION:
            choice = self.strategy.choose_color(ctx)
            return AdapterAction(AdapterActionType.CHOOSE_COLOR, {"choice": choice})

        if state == LiveUIState.WAIT_HIGHER_LOWER_DECISION:
            if not self._try_inject_cards_up_to(snapshot, slot=0):
                self._card_wait_ticks += 1
                if self._card_wait_ticks < CARD_DETECT_MAX_RETRIES:
                    return AdapterAction(AdapterActionType.WAIT)
            choice = self.strategy.choose_higher_lower(ctx)
            return AdapterAction(AdapterActionType.CHOOSE_HIGHER_LOWER, {"choice": choice})

        if state == LiveUIState.WAIT_INSIDE_OUTSIDE_DECISION:
            if not self._try_inject_cards_up_to(snapshot, slot=1):
                self._card_wait_ticks += 1
                if self._card_wait_ticks < CARD_DETECT_MAX_RETRIES:
                    return AdapterAction(AdapterActionType.WAIT)
            choice = self.strategy.choose_inside_outside(ctx)
            return AdapterAction(AdapterActionType.CHOOSE_INSIDE_OUTSIDE, {"choice": choice})

        if state == LiveUIState.WAIT_SUIT_DECISION:
            # Best effort: inject all 3 cards if detectable
            self._try_inject_cards_up_to(snapshot, slot=2)
            choice = self.strategy.choose_suit(ctx)
            return AdapterAction(AdapterActionType.CHOOSE_SUIT, {"choice": choice})

        return AdapterAction(AdapterActionType.WAIT)
