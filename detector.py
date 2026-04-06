from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from models import Card, Rank, RoundState, Suit
from vision import Region


@dataclass(frozen=True, slots=True)
class DetectedCard:
    card: Card
    confidence: float
    source: str = "unknown"


@dataclass(frozen=True, slots=True)
class ControlAvailability:
    can_click_red: bool = False
    can_click_black: bool = False
    can_click_higher: bool = False
    can_click_lower: bool = False
    can_click_inside: bool = False
    can_click_outside: bool = False
    can_click_spades: bool = False
    can_click_hearts: bool = False
    can_click_clubs: bool = False
    can_click_diamonds: bool = False
    round_finished: bool = False


class CardDetector:
    """Detects cards from already-cropped slot images.

    This skeleton intentionally does not implement real CV logic yet.
    The recommended first implementation is template-based recognition
    on fixed slot images from your screenshots.
    """

    def detect_card_at(self, image, slot_region: Region) -> Optional[DetectedCard]:
        slot_image = self._crop_slot(image, slot_region)
        return self.detect_card(slot_image)

    def detect_card(self, slot_image) -> Optional[DetectedCard]:
        rank = self.detect_rank(slot_image)
        suit = self.detect_suit(slot_image)

        if rank is None or suit is None:
            return None

        return DetectedCard(
            card=Card(rank=rank, suit=suit),
            confidence=1.0,
            source="template_stub",
        )

    def detect_rank(self, slot_image) -> Optional[Rank]:
        raise NotImplementedError("Implement rank detection using templates or another CV approach.")

    def detect_suit(self, slot_image) -> Optional[Suit]:
        raise NotImplementedError("Implement suit detection using templates or another CV approach.")

    def _crop_slot(self, image, region: Region):
        if hasattr(image, "crop"):
            return image.crop((region.left, region.top, region.right, region.bottom))
        raise RuntimeError("Image object does not support crop().")


class StateDetector:
    """Detects the current game step from the UI."""
    def detect_round_state(self, image) -> Optional[RoundState]:
        raise NotImplementedError("Implement state detection from UI markers / buttons / labels.")


class ControlDetector:
    """Detects which actions are currently available/clickable."""
    def detect_controls(self, image) -> ControlAvailability:
        raise NotImplementedError("Implement button/control availability detection.")