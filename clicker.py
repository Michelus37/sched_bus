from __future__ import annotations

import time

import pyautogui

from models import ColorGroup, HigherLowerGuess, InOutGuess, Suit

# ── Coordinate constants ──────────────────────────────────────────────────────
# Derived from detector.py panel regions and measured template pixel positions.
# All coordinates are absolute screen positions for a 1920×1080 game window.

# Ready button — detector READY_REGION (860, 680, 1064, 720), template 204×40
_READY = (962, 700)

# 2-button panels (color / higher_lower / inside_outside)
# detector PANELS region (780, 730, 1140, 850), template 360×120
# Button 1 (Red / Higher / Inside):   center at template y≈29  → screen y = 730+29 = 759
# Button 2 (Black / Lower / Outside): center at template y≈76  → screen y = 730+76 = 806
_PANEL_X = 960
_PANEL_BTN1_Y = 759
_PANEL_BTN2_Y = 806

# Suit panel — detector region (813, 748, 1107, 920), template 294×172
# 4 buttons stacked (~43 px each)
# Hearts:   template center y≈21  → screen y = 748+21 = 769
# Clubs:    template center y≈64  → screen y = 748+64 = 812
# Diamonds: template center y≈107 → screen y = 748+107 = 855
# Spades:   template center y≈150 → screen y = 748+150 = 898
_SUIT_X = 960
_SUIT_Y: dict[Suit, int] = {
    Suit.HEARTS:   769,
    Suit.CLUBS:    812,
    Suit.DIAMONDS: 855,
    Suit.SPADES:   898,
}


class MouseClicker:
    """Translates game decisions into mouse clicks via pyautogui.

    Args:
        offset:     (x, y) of the game window's top-left corner on screen.
                    All template coordinates are window-relative, so this is
                    added to every click to get the absolute screen position.
        pre_delay:  seconds to wait before each click (lets UI animations settle).
        post_delay: seconds to wait after each click.
        dry_run:    if True, log intended clicks without moving the mouse.
    """

    def __init__(
        self,
        offset: tuple[int, int] = (0, 0),
        pre_delay: float = 0.3,
        post_delay: float = 0.1,
        dry_run: bool = False,
    ) -> None:
        self.offset = offset
        self.pre_delay = pre_delay
        self.post_delay = post_delay
        self.dry_run = dry_run

    def _click(self, x: int, y: int, label: str = "") -> None:
        ax, ay = x + self.offset[0], y + self.offset[1]
        if self.dry_run:
            print(f"[DRY-RUN] click {label} at ({ax}, {ay})")
            return
        time.sleep(self.pre_delay)
        pyautogui.click(ax, ay)
        time.sleep(self.post_delay)

    def click_ready(self) -> None:
        self._click(*_READY, label="Ready")

    def click_color(self, choice: ColorGroup) -> None:
        y = _PANEL_BTN1_Y if choice == ColorGroup.RED else _PANEL_BTN2_Y
        self._click(_PANEL_X, y, label=f"Color:{choice.name}")

    def click_higher_lower(self, choice: HigherLowerGuess) -> None:
        y = _PANEL_BTN1_Y if choice == HigherLowerGuess.HIGHER else _PANEL_BTN2_Y
        self._click(_PANEL_X, y, label=f"HL:{choice.name}")

    def click_inside_outside(self, choice: InOutGuess) -> None:
        y = _PANEL_BTN1_Y if choice == InOutGuess.INSIDE else _PANEL_BTN2_Y
        self._click(_PANEL_X, y, label=f"IO:{choice.name}")

    def click_suit(self, choice: Suit) -> None:
        self._click(_SUIT_X, _SUIT_Y[choice], label=f"Suit:{choice.name}")
