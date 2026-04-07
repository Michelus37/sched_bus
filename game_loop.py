from __future__ import annotations

import logging
import time

from clicker import MouseClicker
from detector import ButtonDetector, CardDetector, StateDetector
from game_reader import GameReader, TableLayout
from live_adapter import AdapterAction, AdapterActionType, LiveAdapter
from strategy import HeuristicStrategy
from vision import PILScreenCapture, Region, find_game_window

log = logging.getLogger(__name__)

# Card slot positions measured from reference screenshots (1920×1080 game content).
# Each slot starts just before the card's top-left corner and covers the full card.
# Spacing between left edges: ~145px.
_CARD_Y      = 422
_CARD_W      = 145
_CARD_H      = 195


def _build_layout() -> TableLayout:
    return TableLayout(
        table_region=Region(0, 0, 1920, 1080),
        card1_region=Region(290, _CARD_Y, _CARD_W, _CARD_H),
        card2_region=Region(435, _CARD_Y, _CARD_W, _CARD_H),
        card3_region=Region(580, _CARD_Y, _CARD_W, _CARD_H),
        card4_region=Region(725, _CARD_Y, _CARD_W, _CARD_H),
    )


POLL_INTERVAL = 0.5       # seconds between polls while waiting for a state change
POST_CLICK_WAIT = 5.0     # seconds to wait after a click for the game to animate/transition


class GameLoop:
    """Main automation loop.

    Polls quickly (POLL_INTERVAL) while waiting for a state to appear.
    After each click, waits POST_CLICK_WAIT seconds for the game to
    animate and transition before taking the next screenshot.
    """

    def __init__(
        self,
        adapter: LiveAdapter,
        clicker: MouseClicker,
    ) -> None:
        self.adapter = adapter
        self.clicker = clicker

    def run(self) -> None:
        log.info("Game loop started. Press Ctrl+C to stop.")
        while True:
            try:
                snapshot, action = self.adapter.tick()
                cards_str = ", ".join(str(c) for c in snapshot.visible_cards) or "none"
                log.info(
                    "state=%-30s action=%-25s cards=[%s]",
                    snapshot.ui_state.name,
                    action.type.name,
                    cards_str,
                )

                if action.type == AdapterActionType.WAIT:
                    time.sleep(POLL_INTERVAL)
                else:
                    self._execute(action)
                    time.sleep(POST_CLICK_WAIT)

            except KeyboardInterrupt:
                log.info("Stopped by user.")
                break
            except Exception as exc:
                log.warning("Tick error: %s", exc)
                time.sleep(POLL_INTERVAL)

    def _execute(self, action: AdapterAction) -> None:
        p = action.payload or {}

        match action.type:
            case AdapterActionType.CLICK_READY:
                self.clicker.click_ready()
            case AdapterActionType.CHOOSE_COLOR:
                self.clicker.click_color(p["choice"])
            case AdapterActionType.CHOOSE_HIGHER_LOWER:
                self.clicker.click_higher_lower(p["choice"])
            case AdapterActionType.CHOOSE_INSIDE_OUTSIDE:
                self.clicker.click_inside_outside(p["choice"])
            case AdapterActionType.CHOOSE_SUIT:
                self.clicker.click_suit(p["choice"])
            case AdapterActionType.WAIT:
                pass


def main(dry_run: bool = False) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
    )

    window = find_game_window("Schedule I")
    log.info("Found game window at (%d, %d) size %dx%d", window.x, window.y, window.width, window.height)

    capture = PILScreenCapture(monitor_region=window)
    layout = _build_layout()

    reader = GameReader(
        capture=capture,
        layout=layout,
        card_detector=CardDetector(debug=False, save_crops=False),
        button_detector=ButtonDetector(debug=False),
        state_detector=StateDetector(),
    )

    adapter = LiveAdapter(reader=reader, strategy=HeuristicStrategy())
    clicker = MouseClicker(offset=(window.x, window.y), dry_run=dry_run)

    GameLoop(adapter=adapter, clicker=clicker).run()


if __name__ == "__main__":
    # Set dry_run=True to test detection without clicking anything
    main(dry_run=False)
