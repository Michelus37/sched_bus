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

# Card slot fractions from CardDetector.CARD_SLOTS, expressed as Region objects
# for a 1920×1080 window.
_W, _H = 1920, 1080


def _frac(x: float, y: float, w: float, h: float) -> Region:
    return Region(int(x * _W), int(y * _H), int(w * _W), int(h * _H))


def _build_layout() -> TableLayout:
    return TableLayout(
        table_region=Region(0, 0, _W, _H),
        card1_region=_frac(0.215, 0.375, 0.115, 0.20),
        card2_region=_frac(0.315, 0.375, 0.115, 0.20),
        card3_region=_frac(0.415, 0.375, 0.115, 0.20),
        card4_region=_frac(0.515, 0.375, 0.115, 0.20),
    )


class GameLoop:
    """Main automation loop.

    Each tick:
      1. Capture screenshot
      2. Detect UI state + visible cards
      3. Ask adapter/strategy for the next action
      4. Execute the click (if any)
      5. Sleep until the next tick
    """

    def __init__(
        self,
        adapter: LiveAdapter,
        clicker: MouseClicker,
        tick_interval: float = 2.0,
    ) -> None:
        self.adapter = adapter
        self.clicker = clicker
        self.tick_interval = tick_interval

    def run(self) -> None:
        log.info("Game loop started. Press Ctrl+C to stop.")
        while True:
            try:
                snapshot, action = self.adapter.tick()
                log.info(
                    "state=%-30s action=%s",
                    snapshot.ui_state.name,
                    action.type.name,
                )
                self._execute(action)
            except KeyboardInterrupt:
                log.info("Stopped by user.")
                break
            except Exception as exc:
                log.warning("Tick error: %s", exc)

            time.sleep(self.tick_interval)

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


def main(dry_run: bool = False, tick_interval: float = 2.0) -> None:
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
        card_detector=CardDetector(debug=False),
        button_detector=ButtonDetector(debug=False),
        state_detector=StateDetector(),
    )

    adapter = LiveAdapter(reader=reader, strategy=HeuristicStrategy())
    clicker = MouseClicker(offset=(window.x, window.y), dry_run=dry_run)

    GameLoop(adapter=adapter, clicker=clicker, tick_interval=tick_interval).run()


if __name__ == "__main__":
    # Set dry_run=True to test detection without clicking anything
    main(dry_run=False)
