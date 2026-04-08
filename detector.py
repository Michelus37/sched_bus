from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image

from models import Card, Rank, Suit


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
class PanelSpec:
    name: str
    template: str
    region: tuple[int, int, int, int]


# ── Button detection ──────────────────────────────────────────────────────────

class ButtonDetector:
    READY_REGION    = (860, 680, 1064, 720)
    READY_TEMPLATE  = "ready.png"
    READY_THRESHOLD = 0.55
    PANEL_THRESHOLD = 0.70

    PANELS = [
        PanelSpec("color",          "color_panel.png",          (780, 730, 1140, 850)),
        PanelSpec("higher_lower",   "higher_lower_panel.png",   (780, 730, 1140, 850)),
        PanelSpec("inside_outside", "inside_outside_panel.png", (780, 730, 1140, 850)),
        PanelSpec("suit",           "suit_panel.png",           (813, 748, 1107, 920)),
    ]

    def __init__(self, template_dir: str | Path = "templates/buttons", debug: bool = False) -> None:
        self.template_dir = Path(template_dir)
        self.debug = debug
        self._cache: dict[str, np.ndarray] = {}

    def detect_buttons(self, image) -> DetectedButtons:
        ready_score = self._score(image, self.READY_TEMPLATE, self.READY_REGION)
        if self.debug:
            print(f"[DEBUG] ready score={ready_score:.4f} threshold={self.READY_THRESHOLD}")

        if (ready_score or 0.0) >= self.READY_THRESHOLD:
            return DetectedButtons(ready_visible=True)

        panel_scores = {
            panel.name: score
            for panel in self.PANELS
            if (score := self._score(image, panel.template, panel.region)) is not None
        }
        if self.debug:
            for name, score in panel_scores.items():
                print(f"[DEBUG] panel {name}: score={score:.4f}")

        if panel_scores:
            best = max(panel_scores, key=panel_scores.get)
            if panel_scores[best] >= self.PANEL_THRESHOLD:
                return self._buttons_for_panel(best)

        return DetectedButtons()

    def _buttons_for_panel(self, panel_name: str) -> DetectedButtons:
        match panel_name:
            case "color":
                return DetectedButtons(red_visible=True, black_visible=True)
            case "higher_lower":
                return DetectedButtons(higher_visible=True, lower_visible=True)
            case "inside_outside":
                return DetectedButtons(inside_visible=True, outside_visible=True)
            case "suit":
                return DetectedButtons(
                    hearts_visible=True, clubs_visible=True,
                    diamonds_visible=True, spades_visible=True,
                )
        return DetectedButtons()

    def _score(self, image, template_name: str, region: tuple[int, int, int, int]) -> Optional[float]:
        template = self._load(template_name)
        if template is None:
            return None

        roi = self._crop_gray(image, region)
        if roi is None:
            return None

        rh, rw = roi.shape[:2]
        th, tw = template.shape[:2]
        if rh < th or rw < tw:
            if self.debug:
                print(f"[DEBUG] ROI too small for {template_name}: roi=({rw}x{rh}) tpl=({tw}x{th})")
            return None

        _, max_val, _, _ = cv2.minMaxLoc(cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED))
        return float(max_val)

    def _load(self, name: str) -> Optional[np.ndarray]:
        if name not in self._cache:
            path = self.template_dir / name
            img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE) if path.exists() else None
            if img is None and self.debug:
                print(f"[DEBUG] missing template: {name}")
            self._cache[name] = img
        return self._cache[name]

    def _crop_gray(self, image, region: tuple[int, int, int, int]) -> Optional[np.ndarray]:
        cropped = image.crop(region)
        if isinstance(cropped, Image.Image):
            return np.array(cropped.convert("L"), dtype=np.uint8)
        return None


# ── State detection ───────────────────────────────────────────────────────────

class StateDetector:
    def __init__(self, button_detector: Optional[ButtonDetector] = None) -> None:
        self.button_detector = button_detector or ButtonDetector()

    def detect_ui_state(self, image) -> LiveUIState:
        return self._from_buttons(self.button_detector.detect_buttons(image))

    def _from_buttons(self, b: DetectedButtons) -> LiveUIState:
        if b.ready_visible:
            return LiveUIState.WAIT_READY
        if b.red_visible or b.black_visible:
            return LiveUIState.WAIT_COLOR_DECISION
        if b.higher_visible or b.lower_visible:
            return LiveUIState.WAIT_HIGHER_LOWER_DECISION
        if b.inside_visible or b.outside_visible:
            return LiveUIState.WAIT_INSIDE_OUTSIDE_DECISION
        if b.hearts_visible or b.clubs_visible or b.diamonds_visible or b.spades_visible:
            return LiveUIState.WAIT_SUIT_DECISION
        return LiveUIState.UNKNOWN


# ── Card detection ────────────────────────────────────────────────────────────

class CardDetector:
    CORNER_CROP_W            = 0.42
    CORNER_CROP_H            = 0.42
    CORNER_MATCH_THRESHOLD   = 0.9
    CARD_PRESENCE_EDGE_THRESHOLD = 1200
    CARD_PRESENCE_DARK_RATIO = 0.02

    def __init__(
        self,
        template_dir: str | Path = "templates/cards_new",
        debug: bool = False,
        save_crops: bool = False,
    ) -> None:
        self.template_dir = Path(template_dir)
        self.debug = debug
        self.save_crops = save_crops
        self._crop_counter = 0
        self._templates: list[tuple[Card, np.ndarray]] = []
        self._load_templates()

    def detect_card_at(self, image, region) -> Optional[DetectedCard]:
        region_box = self._to_box(region)
        roi = image.crop((region_box[0], region_box[1],
                          region_box[0] + region_box[2], region_box[1] + region_box[3]))

        if self.save_crops:
            roi.save(Path(f"_dbg_crop_{self._crop_counter:04d}_{region_box[0]}x{region_box[1]}.png"))
            self._crop_counter += 1

        if not self._card_present(roi):
            if self.debug:
                print(f"[DEBUG] no card present in region={region_box}")
            return None

        card, score = self._match_corner(roi)
        if card is None:
            if self.debug:
                print(f"[DEBUG] card visible but not recognized in region={region_box}")
            return None

        if score < self.CORNER_MATCH_THRESHOLD:
            print(f"[WARN] low confidence match: {card} score={score:.3f}")

        return DetectedCard(card=card, confidence=score, source=str(region_box))

    # ── Internal ──────────────────────────────────────────────────────────────

    def _load_templates(self) -> None:
        if not self.template_dir.exists():
            print(f"[WARN] template directory not found: {self.template_dir}")
            return

        for path in sorted(self.template_dir.glob("*.png")):
            card = self._parse_name(path.stem)
            if card is None:
                continue
            img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            self._templates.append((card, img))
            if self.debug:
                print(f"[DEBUG] loaded: {path.name} → {card}")

    def _parse_name(self, stem: str) -> Optional[Card]:
        parts = [p for p in stem.lower().replace("-", "_").split("_") if p]
        if len(parts) < 2:
            return None
        rank = self._parse_rank(parts[0])
        # Try parts[1] first so variant suffixes like _2 or _alt are ignored
        suit = self._parse_suit(parts[1]) or self._parse_suit("_".join(parts[1:]))
        if rank is None or suit is None:
            return None
        return Card(rank=rank, suit=suit)

    def _parse_rank(self, s: str) -> Optional[Rank]:
        return {
            "a": Rank.ACE,   "ace": Rank.ACE,
            "k": Rank.KING,  "king": Rank.KING,
            "q": Rank.QUEEN, "queen": Rank.QUEEN,
            "j": Rank.JACK,  "jack": Rank.JACK,
            "t": Rank.TEN,   "10": Rank.TEN,   "ten": Rank.TEN,
            "9": Rank.NINE,  "8": Rank.EIGHT,  "7": Rank.SEVEN,
            "6": Rank.SIX,   "5": Rank.FIVE,   "4": Rank.FOUR,
            "3": Rank.THREE, "2": Rank.TWO,
        }.get(s)

    def _parse_suit(self, s: str) -> Optional[Suit]:
        return {
            "s": Suit.SPADES,   "spades": Suit.SPADES,   "pik": Suit.SPADES,
            "h": Suit.HEARTS,   "hearts": Suit.HEARTS,   "herz": Suit.HEARTS,
            "c": Suit.CLUBS,    "clubs": Suit.CLUBS,     "kreuz": Suit.CLUBS,
            "d": Suit.DIAMONDS, "diamonds": Suit.DIAMONDS, "karo": Suit.DIAMONDS,
        }.get(s)

    def _card_present(self, roi) -> bool:
        gray = np.array(roi.convert("L"), dtype=np.uint8)
        edge_count = int(np.count_nonzero(cv2.Canny(gray, 50, 150)))
        dark_ratio  = float(np.mean(gray < 220))
        if self.debug:
            print(f"[DEBUG] presence edge_count={edge_count} dark_ratio={dark_ratio:.3f}")
        return edge_count > self.CARD_PRESENCE_EDGE_THRESHOLD or dark_ratio > self.CARD_PRESENCE_DARK_RATIO

    def _match_corner(self, roi) -> tuple[Optional[Card], float]:
        if not self._templates:
            return None, 0.0
        gray = np.array(roi.convert("L"), dtype=np.uint8)
        h, w = gray.shape
        corner = gray[:int(h * self.CORNER_CROP_H), :int(w * self.CORNER_CROP_W)]
        return self._best_match(corner)

    def _best_match(self, roi_gray: np.ndarray) -> tuple[Optional[Card], float]:
        best_card: Optional[Card] = None
        best_score = 0.0
        for card, template in self._templates:
            if roi_gray.shape[0] < template.shape[0] or roi_gray.shape[1] < template.shape[1]:
                continue
            _, score, _, _ = cv2.minMaxLoc(cv2.matchTemplate(roi_gray, template, cv2.TM_CCOEFF_NORMED))
            if score > best_score:
                best_score = float(score)
                best_card = card
        if self.debug:
            print(f"[DEBUG] best match: {best_card} score={best_score:.3f}")
        return best_card, best_score

    def _to_box(self, region) -> tuple[int, int, int, int]:
        if hasattr(region, "x"):
            return (int(region.x), int(region.y), int(region.width), int(region.height))
        if isinstance(region, tuple) and len(region) == 4:
            return region
        raise RuntimeError(f"Unsupported region type: {type(region)}")
