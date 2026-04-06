from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from detector import (
    CardDetector,
    DetectedButtons,
    DetectedCard,
    LiveUIState,
    StateDetector,
    ButtonDetector,
)
from models import Card
from vision import Region, ScreenCapture


@dataclass(frozen=True, slots=True)
class TableLayout:
    table_region: Region

    card1_region: Region
    card2_region: Region
    card3_region: Region
    card4_region: Region

    # Optional: button regions later, if needed for matching
    ready_button_region: Optional[Region] = None
    decision_panel_region: Optional[Region] = None


@dataclass(slots=True)
class LiveGameSnapshot:
    ui_state: LiveUIState
    visible_cards: list[Card] = field(default_factory=list)
    detected_cards: list[DetectedCard] = field(default_factory=list)
    buttons: Optional[DetectedButtons] = None


class GameReader:
    """Reads the real game screen and returns a structured snapshot."""

    def __init__(
        self,
        capture: ScreenCapture,
        layout: TableLayout,
        card_detector: Optional[CardDetector] = None,
        button_detector: Optional[ButtonDetector] = None,
        state_detector: Optional[StateDetector] = None,
    ) -> None:
        self.capture = capture
        self.layout = layout
        self.card_detector = card_detector or CardDetector()
        self.button_detector = button_detector or ButtonDetector()
        self.state_detector = state_detector or StateDetector(self.button_detector)

    def read_snapshot(self) -> LiveGameSnapshot:
        table_image = self.capture.capture_region(self.layout.table_region)

        buttons = self._safe_detect_buttons(table_image)
        ui_state = self._safe_detect_ui_state(table_image)
        detected_cards = self._detect_cards(table_image)
        visible_cards = [entry.card for entry in detected_cards]

        return LiveGameSnapshot(
            ui_state=ui_state,
            visible_cards=visible_cards,
            detected_cards=detected_cards,
            buttons=buttons,
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

    def _safe_detect_buttons(self, table_image) -> Optional[DetectedButtons]:
        try:
            return self.button_detector.detect_buttons(table_image)
        except NotImplementedError:
            return None

    def _safe_detect_ui_state(self, table_image) -> LiveUIState:
        try:
            return self.state_detector.detect_ui_state(table_image)
        except NotImplementedError:
            return LiveUIState.UNKNOWN