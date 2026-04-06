from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from detector import LiveUIState
from game_reader import GameReader, LiveGameSnapshot


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


class LiveAdapter:
    """Bridges the live UI state to later decision logic and input actions.

    Early version:
    - classify what should happen next
    - do not click yet
    - do not mutate engine state yet
    """

    def __init__(self, reader: GameReader) -> None:
        self.reader = reader

    def tick(self) -> tuple[LiveGameSnapshot, AdapterAction]:
        snapshot = self.reader.read_snapshot()
        action = self._decide_next_action(snapshot)
        return snapshot, action

    def _decide_next_action(self, snapshot: LiveGameSnapshot) -> AdapterAction:
        state = snapshot.ui_state

        if state == LiveUIState.WAIT_READY:
            return AdapterAction(AdapterActionType.CLICK_READY)

        if state == LiveUIState.WAIT_COLOR_DECISION:
            return AdapterAction(AdapterActionType.CHOOSE_COLOR)

        if state == LiveUIState.WAIT_HIGHER_LOWER_DECISION:
            return AdapterAction(AdapterActionType.CHOOSE_HIGHER_LOWER)

        if state == LiveUIState.WAIT_INSIDE_OUTSIDE_DECISION:
            return AdapterAction(AdapterActionType.CHOOSE_INSIDE_OUTSIDE)

        if state == LiveUIState.WAIT_SUIT_DECISION:
            return AdapterAction(AdapterActionType.CHOOSE_SUIT)

        return AdapterAction(AdapterActionType.WAIT)