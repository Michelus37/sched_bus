from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np
from PIL import Image

from models import *
print(f"DEBUG: imported Rank = {Rank}")


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
class GroupSpec:
    name: str
    region: tuple[int, int, int, int]
    templates: tuple[str, ...]
    min_best_score: float
    min_margin: float


@dataclass(frozen=True, slots=True)
class PanelSpec:
    name: str
    template: str
    region: tuple[int, int, int, int]


@dataclass(frozen=True, slots=True)
class CardSlot:
    name: str
    x: float
    y: float
    width: float
    height: float

    def to_region(self, image_width: int, image_height: int) -> tuple[int, int, int, int]:
        return (
            int(self.x * image_width),
            int(self.y * image_height),
            int(self.width * image_width),
            int(self.height * image_height),
        )


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
    READY_THRESHOLD = 0.55
    
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
        ready_score = self._score_template(image, self.READY_TEMPLATE, self.READY_REGION)
        ready_visible = (ready_score or 0.0) >= self.READY_THRESHOLD

        if self.debug:
            print(f"[DEBUG] ready score={ready_score:.4f} threshold={self.READY_THRESHOLD} visible={ready_visible}")

        if ready_visible:
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
    CARD_SLOTS = [
        CardSlot("card1", 0.215, 0.375, 0.115, 0.20),
        CardSlot("card2", 0.315, 0.375, 0.115, 0.20),
        CardSlot("card3", 0.415, 0.375, 0.115, 0.20),
    ]

    CARD_TEMPLATE_DIR = "templates/cards"
    CARD_TEMPLATE_THRESHOLD = 0.70
    CARD_PRESENCE_EDGE_THRESHOLD = 1200
    CARD_PRESENCE_DARK_RATIO = 0.02

    # Fraction of the card ROI to crop as the top-left corner for matching
    CORNER_CROP_W = 0.42
    CORNER_CROP_H = 0.42
    CORNER_MATCH_THRESHOLD = 0.85

    def __init__(self, template_dir: str | Path = CARD_TEMPLATE_DIR, debug: bool = False, save_crops: bool = False) -> None:
        self.template_dir = Path(template_dir)
        self.debug = debug
        self.save_crops = save_crops
        self._crop_counter = 0
        self._template_cache: dict[str, np.ndarray] = {}
        self._full_card_templates: list[tuple[Card, np.ndarray]] = []
        self._rank_templates: list[tuple[Rank, np.ndarray]] = []
        self._suit_templates: list[tuple[Suit, np.ndarray]] = []
        self._corner_templates: list[tuple[Card, np.ndarray]] = []
        self._load_card_templates()

    def detect_cards(self, image) -> list[DetectedCard]:
        image_width, image_height = self._get_image_size(image)
        results: list[DetectedCard] = []

        for slot in self.CARD_SLOTS:
            region = slot.to_region(image_width, image_height)
            detected = self.detect_card_at(image, region)
            if detected is not None:
                results.append(detected)

        return results

    def detect_card_at(self, image, region) -> Optional[DetectedCard]:
        region_box = self._normalize_region(region)
        roi = self._crop_region(image, region_box)
        if roi is None:
            return None

        if self.save_crops:
            crop_path = Path(f"_dbg_crop_{self._crop_counter:04d}_{region_box[0]}x{region_box[1]}.png")
            if hasattr(roi, "save"):
                roi.save(crop_path)
            self._crop_counter += 1

        if not self._is_card_present(roi):
            if self.debug:
                print(f"[DEBUG] no card present in region={region_box}")
            return None

        card, score = self._match_corner_template(roi)
        if card is not None:
            return DetectedCard(card=card, confidence=score, source=str(region_box))

        card, score = self._match_full_card(roi)
        if card is not None:
            return DetectedCard(card=card, confidence=score, source=str(region_box))

        card, score = self._match_rank_suit(roi)
        if card is not None:
            return DetectedCard(card=card, confidence=score, source=str(region_box))

        if self.debug:
            print(f"[DEBUG] card visible but not recognized in region={region_box}")

        return None

    def _normalize_region(self, region) -> tuple[int, int, int, int]:
        if hasattr(region, "x") and hasattr(region, "y"):
            return (int(region.x), int(region.y), int(region.width), int(region.height))
        if isinstance(region, tuple) and len(region) == 4:
            return region
        raise RuntimeError("Unsupported region object. Expected Region or tuple[x, y, width, height].")

    def _get_image_size(self, image) -> tuple[int, int]:
        if hasattr(image, "size"):
            return image.size
        raise RuntimeError("Unsupported image object. Expected PIL.Image.")

    def _is_card_present(self, roi) -> bool:
        if not hasattr(roi, "convert"):
            return False

        grayscale = np.array(roi.convert("L"), dtype=np.uint8)
        dark_ratio = float(np.mean(grayscale < 220))
        edges = cv2.Canny(grayscale, 50, 150)
        edge_count = int(np.count_nonzero(edges))

        if self.debug:
            print(
                f"[DEBUG] card presence dark_ratio={dark_ratio:.3f} edge_count={edge_count} "
                f"roi=({grayscale.shape[1]}x{grayscale.shape[0]})"
            )

        return edge_count > self.CARD_PRESENCE_EDGE_THRESHOLD or dark_ratio > self.CARD_PRESENCE_DARK_RATIO

    def _load_card_templates(self) -> None:
        if not self.template_dir.exists():
            if self.debug:
                print(f"[DEBUG] missing card template directory: {self.template_dir}")
            return

        for template_path in sorted(self.template_dir.glob("*.png")):
            card = self._parse_card_template_name(template_path.stem)
            if card is None:
                if self.debug:
                    print(f"[DEBUG] skipped template (parse failed): {template_path.name}")
                continue

            template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
            if template is None:
                if self.debug:
                    print(f"[DEBUG] failed to load template image: {template_path.name}")
                continue

            self._full_card_templates.append((card, template))
            if self.debug:
                print(f"[DEBUG] loaded full card template: {template_path.name}")

        ranks_dir = self.template_dir / "ranks"
        suits_dir = self.template_dir / "suits"

        if ranks_dir.exists():
            if self.debug:
                print(f"[DEBUG] loading rank templates from {ranks_dir}")
            for template_path in sorted(ranks_dir.glob("*.png")):
                rank = self._parse_rank_template_name(template_path.stem)
                if rank is None:
                    if self.debug:
                        print(f"[DEBUG] failed to parse rank from {template_path.name}")
                    continue

                template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
                if template is None:
                    if self.debug:
                        print(f"[DEBUG] failed to load rank template {template_path.name}")
                    continue

                self._rank_templates.append((rank, template))
                if self.debug:
                    print(f"[DEBUG] loaded rank template: {template_path.name} -> {rank}")

        if suits_dir.exists():
            if self.debug:
                print(f"[DEBUG] loading suit templates from {suits_dir}")
            for template_path in sorted(suits_dir.glob("*.png")):
                suit = self._parse_suit_template_name(template_path.stem)
                if suit is None:
                    if self.debug:
                        print(f"[DEBUG] failed to parse suit from {template_path.name}")
                    continue

                template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
                if template is None:
                    if self.debug:
                        print(f"[DEBUG] failed to load suit template {template_path.name}")
                    continue

                self._suit_templates.append((suit, template))
                if self.debug:
                    print(f"[DEBUG] loaded suit template: {template_path.name} -> {suit}")

        corners_dir = self.template_dir.parent / "cards_new"
        if corners_dir.exists():
            if self.debug:
                print(f"[DEBUG] loading corner templates from {corners_dir}")
            for template_path in sorted(corners_dir.glob("*.png")):
                card = self._parse_card_template_name(template_path.stem)
                if card is None:
                    if self.debug:
                        print(f"[DEBUG] failed to parse card from {template_path.name}")
                    continue

                template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
                if template is None:
                    if self.debug:
                        print(f"[DEBUG] failed to load corner template {template_path.name}")
                    continue

                self._corner_templates.append((card, template))
                if self.debug:
                    print(f"[DEBUG] loaded corner template: {template_path.name} -> {card}")

    def _parse_card_template_name(self, stem: str) -> Optional[Card]:
        if not stem:
            return None

        text = stem.lower().replace("-", "_").replace(" ", "_")
        parts = [part for part in text.split("_") if part]

        # Handle format: "a_diamonds" or "10_clubs"
        if len(parts) >= 2:
            rank_str = parts[0]
            suit_str = "_".join(parts[1:])  # in case suit contains underscore (unlikely)
        else:
            # Single part without underscore - skip, it's not a full card template
            return None

        rank = self._parse_rank(rank_str)
        suit = self._parse_suit(suit_str)

        if self.debug:
            print(f"[DEBUG] parsing '{stem}' -> rank_str='{rank_str}' rank={rank} suit_str='{suit_str}' suit={suit}")

        if rank is None or suit is None:
            if self.debug:
                print(f"[DEBUG] Failed to parse card from stem '{stem}': rank={rank} suit={suit}")
            return None

        return Card(rank=rank, suit=suit)

    def _parse_rank_template_name(self, stem: str) -> Optional[Rank]:
        text = stem.lower().replace("-", "_").replace(" ", "_")
        return self._parse_rank(text)

    def _parse_suit_template_name(self, stem: str) -> Optional[Suit]:
        text = stem.lower().replace("-", "_").replace(" ", "_")
        return self._parse_suit(text)

    def _parse_rank(self, rank_str: str) -> Optional[Rank]:
        if self.debug:
            print(f"[DEBUG] _parse_rank called with '{rank_str}', Rank = {Rank}")
        rank_map = {
            "a": "ACE",
            "ace": "ACE",
            "k": "KING",
            "king": "KING",
            "q": "QUEEN",
            "queen": "QUEEN",
            "j": "JACK",
            "jack": "JACK",
            "t": "TEN",
            "10": "TEN",
            "ten": "TEN",
            "9": "NINE",
            "8": "EIGHT",
            "7": "SEVEN",
            "6": "SIX",
            "5": "FIVE",
            "4": "FOUR",
            "3": "THREE",
            "2": "TWO",
        }
        rank_name = rank_map.get(rank_str)
        if rank_name is None:
            return None
        if self.debug:
            print(f"[DEBUG] _parse_rank('{rank_str}') -> rank_name='{rank_name}'")
        rank = getattr(Rank, rank_name, None)
        if self.debug:
            print(f"[DEBUG] getattr(Rank, '{rank_name}') = {rank}")
        return rank

    def _parse_suit(self, suit_str: str) -> Optional[Suit]:
        suit_map = {
            "s": "SPADES",
            "spades": "SPADES",
            "pik": "SPADES",
            "h": "HEARTS",
            "hearts": "HEARTS",
            "herz": "HEARTS",
            "c": "CLUBS",
            "clubs": "CLUBS",
            "kreuz": "CLUBS",
            "d": "DIAMONDS",
            "diamonds": "DIAMONDS",
            "karo": "DIAMONDS",
        }
        suit_name = suit_map.get(suit_str)
        if suit_name is None:
            return None
        return getattr(Suit, suit_name)

    def _match_corner_template(self, roi) -> tuple[Optional[Card], float]:
        """Match the top-left corner of the card ROI against combined rank+suit templates."""
        if not self._corner_templates:
            return None, 0.0

        gray = np.array(roi.convert("L"), dtype=np.uint8)
        h, w = gray.shape
        corner = gray[:int(h * self.CORNER_CROP_H), :int(w * self.CORNER_CROP_W)]

        card, score = self._best_template_match(self._corner_templates, corner)

        if self.debug:
            print(f"[DEBUG] corner match: card={card} score={score:.3f}")

        if score >= self.CORNER_MATCH_THRESHOLD:
            return card, score

        return None, 0.0

    def _match_full_card(self, roi) -> tuple[Optional[Card], float]:
        if not self._full_card_templates:
            return None, 0.0

        roi_gray = np.array(roi.convert("L"), dtype=np.uint8)
        best_card: Optional[Card] = None
        best_score = 0.0

        for card, template in self._full_card_templates:
            if roi_gray.shape[0] < template.shape[0] or roi_gray.shape[1] < template.shape[1]:
                continue

            result = cv2.matchTemplate(roi_gray, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            if max_val > best_score:
                best_score = float(max_val)
                best_card = card

        if best_score >= self.CARD_TEMPLATE_THRESHOLD:
            return best_card, best_score

        return None, 0.0

    def _match_rank_suit(self, roi) -> tuple[Optional[Card], float]:
        if not self._rank_templates or not self._suit_templates:
            return None, 0.0

        region = roi.convert("L")
        width, height = region.size
        corner = region.crop((0, 0, int(width * 0.32), int(height * 0.24)))

        rank, rank_score = self._best_template_match(self._rank_templates, corner)
        suit, suit_score = self._best_template_match(self._suit_templates, corner)

        if rank is None or suit is None:
            return None, 0.0

        if rank_score < 0.4 or suit_score < 0.4:
            if self.debug:
                print(
                    f"[DEBUG] low rank/suit score rank={rank_score:.3f} suit={suit_score:.3f}"
                )
            return None, 0.0

        combined_score = float((rank_score + suit_score) / 2.0)
        return Card(rank=rank, suit=suit), combined_score

    def _best_template_match(
        self,
        templates: list[tuple[Any, np.ndarray]],
        roi_gray,
    ) -> tuple[Optional[Any], float]:
        if not templates:
            return None, 0.0

        if isinstance(roi_gray, Image.Image):
            roi_gray = np.array(roi_gray.convert("L"), dtype=np.uint8)

        best_item = None
        best_score = 0.0

        for item, template in templates:
            if roi_gray.shape[0] < template.shape[0] or roi_gray.shape[1] < template.shape[1]:
                continue

            result = cv2.matchTemplate(roi_gray, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            if max_val > best_score:
                best_score = float(max_val)
                best_item = item

        return best_item, best_score

    def _crop_region(self, image, region: tuple[int, int, int, int]):
        if not hasattr(image, "crop"):
            raise RuntimeError("Image object does not support crop().")

        left, top, width, height = region
        return image.crop((left, top, left + width, top + height))
