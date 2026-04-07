from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image

from models import Card
from vision import Region


class LiveUIState(Enum):
    UNKNOWN = auto()
    WAIT_READY = auto()
    WAIT_COLOR_DECISION = auto()
    WAIT_HIGHER_LOWER_DECISION = auto()
    WAIT_INSIDE_OUTSIDE_DECISION = auto()
    WAIT_SUIT_DECISION = auto()
    TRANSITION = auto()


@dataclass(frozen=True, slots=True)
class DetectedCard:
    card: Card
    confidence: float
    source: str = "unknown"


@dataclass(frozen=True, slots=True)
class DetectedButtons:
    ready_visible: bool = False

    red_visible: bool = False
    black_visible: bool = False

    higher_visible: bool = False
    lower_visible: bool = False

    inside_visible: bool = False
    outside_visible: bool = False

    hearts_visible: bool = False
    clubs_visible: bool = False
    diamonds_visible: bool = False
    spades_visible: bool = False

    forfeit_visible: bool = False


@dataclass(frozen=True, slots=True)
class MatchResult:
    template_name: str
    score: float
    second_score: float
    margin: float


@dataclass(frozen=True, slots=True)
class PanelSpec:
    name: str
    template: str
    region: tuple[int, int, int, int]


class ButtonDetector:
    """
    Bild -> DetectedButtons

    OpenCV-Version:
    - Ready separat erkennen
    - Danach konkurrieren die Gruppen gegeneinander
    - Genau eine Gruppe darf gewinnen
    - Innerhalb der Gewinnergruppe wird genau ein Button aktiviert

    score:
    - cv2.matchTemplate(..., TM_CCOEFF_NORMED)
    - höher ist besser
    """

    READY_REGION = (860, 680, 1064, 720)
    READY_TEMPLATE = "ready.png"
    READY_THRESHOLD = 0.70
    
    PANELS = [
        PanelSpec("color", "color_panel.png", (780, 730, 1140, 850)),
        PanelSpec("higher_lower", "higher_lower_panel.png", (780, 730, 1140, 850)),
        PanelSpec("inside_outside", "inside_outside_panel.png", (780, 730, 1140, 850)),
        PanelSpec("suit", "suit_panel.png", (813, 748, 1107, 920)),
    ]

    PANELS = [
        PanelSpec("color", "color_panel.png", (780, 730, 1140, 850)),
        PanelSpec("higher_lower", "higher_lower_panel.png", (780, 730, 1140, 850)),
        PanelSpec("inside_outside", "inside_outside_panel.png", (780, 730, 1140, 850)),
        PanelSpec("suit", "suit_panel.png", (813, 748, 1107, 920)),
    ]

    def __init__(self, template_dir: str | Path = "templates/buttons", debug: bool = False) -> None:
        self.template_dir = Path(template_dir)
        self.debug = debug
        self._template_cache: dict[str, np.ndarray] = {}

    def detect_buttons(self, image) -> DetectedButtons:
        ready_visible = self._detect_in_region(
            image=image,
            template_name=self.READY_TEMPLATE,
            region=self.READY_REGION,
            threshold=self.READY_THRESHOLD,
        )

        if ready_visible:
            if self.debug:
                print("[DEBUG] ready detected")
            return DetectedButtons(ready_visible=True)

        # Match panel templates to determine the game state
        panel_scores = {}
        for panel in self.PANELS:
            score = self._score_template(image, panel.template, panel.region)
            if score is not None:
                panel_scores[panel.name] = score
                if self.debug:
                    print(f"[DEBUG] panel {panel.name}: score={score:.4f}")

        if panel_scores:
            best_panel = max(panel_scores, key=panel_scores.get)
            best_score = panel_scores[best_panel]
            if self.debug:
                print(f"[DEBUG] best panel {best_panel}: score={best_score:.4f}")
            if best_score > 0.7:  # Panel detection threshold
                return self._build_result_for_panel(best_panel)

        if self.debug:
            print("[DEBUG] no panel detected")

        return DetectedButtons()

    def _build_result_for_panel(self, panel_name: str) -> DetectedButtons:
        if panel_name == "color":
            return DetectedButtons(red_visible=True, black_visible=True)
        if panel_name == "higher_lower":
            return DetectedButtons(higher_visible=True, lower_visible=True)
        if panel_name == "inside_outside":
            return DetectedButtons(inside_visible=True, outside_visible=True)
        if panel_name == "suit":
            return DetectedButtons(
                hearts_visible=True,
                clubs_visible=True,
                diamonds_visible=True,
                spades_visible=True,
            )
        return DetectedButtons()

    def _best_match(self, image, group: GroupSpec) -> Optional[MatchResult]:
        scores: list[tuple[str, float]] = []

        for template_name in group.templates:
            score = self._score_template(
                image=image,
                template_name=template_name,
                region=group.region,
            )
            if score is None:
                continue
            scores.append((template_name, score))

        if not scores:
            return None

        scores.sort(key=lambda item: item[1], reverse=True)

        best_name, best_score = scores[0]
        second_score = scores[1][1] if len(scores) > 1 else None
        margin = (best_score - second_score) if second_score is not None else 9999.0

        if self.debug:
            joined = ", ".join(f"{name}={score:.4f}" for name, score in scores)
            print(f"[DEBUG] group {group.name}: {joined}")
            print(
                f"[DEBUG] best={best_name} score={best_score:.4f} "
                f"second={second_score:.4f} margin={margin:.4f}"
            )

        return MatchResult(
            template_name=best_name,
            score=best_score,
            second_score=second_score,
            margin=margin,
        )

    def _score_template(
        self,
        image,
        template_name: str,
        region: tuple[int, int, int, int],
    ) -> Optional[float]:
        template = self._load_template_gray(template_name)
        if template is None:
            return None

        roi = self._crop_region_gray(image, region)
        if roi is None:
            return None

        roi_h, roi_w = roi.shape[:2]
        tpl_h, tpl_w = template.shape[:2]

        if roi_h < tpl_h or roi_w < tpl_w:
            if self.debug:
                print(
                 f"[DEBUG] ROI too small for template {template_name}: "
                 f"roi=({roi_w}x{roi_h}) tpl=({tpl_w}x{tpl_h})"
                 )
            return None

        result = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)
        _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)

        if self.debug:
            print(
                f"[DEBUG] {template_name}: "
                f"score={max_val:.4f} "
                f"roi=({roi_w}x{roi_h}) "
                f"tpl=({tpl_w}x{tpl_h}) "
                f"loc={max_loc}"
            )

        return float(max_val)

    def _detect_in_region(
        self,
        image,
        template_name: str,
        region: tuple[int, int, int, int],
        threshold: float,
    ) -> bool:
        score = self._score_template(
            image=image,
            template_name=template_name,
            region=region,
        )

        if score is None:
            return False

        if self.debug:
            print(f"[DEBUG] {template_name}: detect score={score:.4f}")

        return score >= threshold

    def _load_template_gray(self, template_name: str) -> Optional[np.ndarray]:
        if template_name in self._template_cache:
            return self._template_cache[template_name]

        template_path = self.template_dir / template_name
        if not template_path.exists():
            if self.debug:
                print(f"[DEBUG] missing template: {template_name}")
            return None

        template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
        if template is None:
            if self.debug:
                print(f"[DEBUG] failed to load template: {template_name}")
            return None

        self._template_cache[template_name] = template
        return template

    def _crop_region_gray(self, image, region: tuple[int, int, int, int]) -> Optional[np.ndarray]:
        if not hasattr(image, "crop"):
            raise RuntimeError("Image object does not support crop().")

        cropped = image.crop(region)

        if isinstance(cropped, Image.Image):
            cropped = cropped.convert("L")
            return np.array(cropped, dtype=np.uint8)

        return None


class StateDetector:
    def __init__(self, button_detector: Optional[ButtonDetector] = None) -> None:
        self.button_detector = button_detector or ButtonDetector()

    def detect_ui_state(self, image) -> LiveUIState:
        buttons = self.button_detector.detect_buttons(image)
        return self.detect_ui_state_from_buttons(buttons)

    def detect_ui_state_from_buttons(self, buttons: DetectedButtons) -> LiveUIState:
        if buttons.ready_visible:
            return LiveUIState.WAIT_READY

        if buttons.red_visible or buttons.black_visible:
            return LiveUIState.WAIT_COLOR_DECISION

        if buttons.higher_visible or buttons.lower_visible:
            return LiveUIState.WAIT_HIGHER_LOWER_DECISION

        if buttons.inside_visible or buttons.outside_visible:
            return LiveUIState.WAIT_INSIDE_OUTSIDE_DECISION

        if (
            buttons.hearts_visible
            or buttons.clubs_visible
            or buttons.diamonds_visible
            or buttons.spades_visible
        ):
            return LiveUIState.WAIT_SUIT_DECISION

        return LiveUIState.UNKNOWN


class CardDetector:
    def detect_card_at_slot(self, image, slot_name: str) -> Optional[DetectedCard]:
        return None