from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from detector import CardDetector, ControlAvailability, ControlDetector, DetectedCard, StateDetector
from models import Card, RoundState
from vision import Region, ScreenCapture


@dataclass(frozen=True, slots=True)
class TableLayout:
    """Defines fixed screen regions for the game table.

    Start with manually measured regions from screenshots.
    """

    table_region: Region
    card1_region: Region
    card2_region: Region
    card3_region: Region
    card4_region: Region


@dataclass(slots=True)
class LiveGameSnapshot:
    state: Optional[RoundState]
    visible_cards: list[Card] = field(default_factory=list)
    detected_cards: list[DetectedCard] = field(default_factory=list)
    controls: Optional[ControlAvailability] = None
    round_finished: bool = False


class GameReader:
    """Reads the visible game state from the real game screen.

    Important:
    - This should only READ from the game.
    - It should not contain game rules.
    - It should not click anything.
    """

    def __init__(
        self,
        capture: ScreenCapture,
        layout: TableLayout,
        card_detector: Optional[CardDetector] = None,
        state_detector: Optional[StateDetector] = None,
        control_detector: Optional[ControlDetector] = None,
    ) -> None:
        self.capture = capture
        self.layout = layout
        self.card_detector = card_detector or CardDetector()
        self.state_detector = state_detector or StateDetector()
        self.control_detector = control_detector or ControlDetector()

    def read_snapshot(self) -> LiveGameSnapshot:
        table_image = self.capture.capture_region(self.layout.table_region)

        state = self._safe_detect_state(table_image)
        detected_cards = self._detect_cards(table_image)
        controls = self._safe_detect_controls(table_image)

        visible_cards = [entry.card for entry in detected_cards]

        round_finished = False
        if controls is not None:
            round_finished = controls.round_finished

        return LiveGameSnapshot(
            state=state,
            visible_cards=visible_cards,
            detected_cards=detected_cards,
            controls=controls,
            round_finished=round_finished,
        )

    def _detect_cards(self, table_image) -> list[DetectedCard]:
        results: list[DetectedCard] = []

        for region in (
            self.layout.card1_region,
            self.layout.card2_region,
            self.layout.card3_region,
            self.layout.card4_region,
        ):
            detected = self.card_detector.detect_card_at(table_image, region)
            if detected is not None:
                results.append(detected)

        return results

    def _safe_detect_state(self, table_image) -> Optional[RoundState]:
        try:
            return self.state_detector.detect_round_state(table_image)
        except NotImplementedError:
            return None

    def _safe_detect_controls(self, table_image) -> Optional[ControlAvailability]:
        try:
            return self.control_detector.detect_controls(table_image)
        except NotImplementedError:
            return None