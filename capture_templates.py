"""
Template capture helper.

Run alongside the game to automatically save corner crops of unrecognised cards.
Each new card is saved as:
    templates/cards_new/_capture_NNNN_<slot>.png

Rename the file to the correct card name afterwards, e.g.:
    K_hearts.png  |  7_spades.png  |  Q_karo.png

Press Ctrl+C to stop.
"""

from __future__ import annotations

import time
from pathlib import Path

from detector import ButtonDetector, CardDetector, LiveUIState, StateDetector
from game_reader import GameReader, TableLayout
from vision import PILScreenCapture, Region, find_game_window

SAVE_DIR  = Path("templates/cards_new")
CARD_Y, CARD_W, CARD_H = 422, 145, 195
CORNER_W, CORNER_H     = 0.42, 0.42

# States that reveal a new card, mapped to the slot to inspect
_CARD_STATES: dict[LiveUIState, tuple[str, int]] = {
    LiveUIState.WAIT_HIGHER_LOWER_DECISION:   ("card1", 0),
    LiveUIState.WAIT_INSIDE_OUTSIDE_DECISION: ("card2", 1),
    LiveUIState.WAIT_SUIT_DECISION:           ("card3", 2),
}


def _crop_corner(roi) -> object:
    w, h = roi.size
    return roi.crop((0, 0, int(w * CORNER_W), int(h * CORNER_H)))


def main() -> None:
    print("Looking for game window…")
    window = find_game_window("Schedule I")
    print(f"Found: {window}\n")

    capture = PILScreenCapture(monitor_region=window)
    card_regions = [
        Region(290, CARD_Y, CARD_W, CARD_H),
        Region(435, CARD_Y, CARD_W, CARD_H),
        Region(580, CARD_Y, CARD_W, CARD_H),
        Region(725, CARD_Y, CARD_W, CARD_H),
    ]
    layout = TableLayout(
        table_region=Region(0, 0, 1920, 1080),
        card1_region=card_regions[0],
        card2_region=card_regions[1],
        card3_region=card_regions[2],
        card4_region=card_regions[3],
    )
    detector = CardDetector()
    reader = GameReader(
        capture=capture,
        layout=layout,
        card_detector=detector,
        button_detector=ButtonDetector(),
        state_detector=StateDetector(),
    )

    counter = 0
    handled: set[LiveUIState] = set()
    last_state = LiveUIState.UNKNOWN

    print("Running — play normally, unknown cards are saved automatically.")
    print("Press Ctrl+C to stop.\n")

    while True:
        try:
            snapshot = reader.read_snapshot()
            state = snapshot.ui_state

            if state != last_state:
                last_state = state
                handled.discard(state)

            if state in _CARD_STATES and state not in handled:
                slot_name, slot_idx = _CARD_STATES[state]
                roi = capture.capture_region(card_regions[slot_idx])
                detected = detector.detect_card_at(roi, (0, 0, roi.size[0], roi.size[1]))

                if detected is not None:
                    print(f"  [{slot_name}] already known: {detected.card}  (score={detected.confidence:.2f})")
                else:
                    path = SAVE_DIR / f"_capture_{counter:04d}_{slot_name}.png"
                    _crop_corner(roi).save(path)
                    print(f"  [{slot_name}] unknown — saved {path.name}  → rename to e.g. K_hearts.png")
                    counter += 1

                handled.add(state)

            time.sleep(0.5)

        except KeyboardInterrupt:
            print(f"\nDone. {counter} new crop(s) saved to {SAVE_DIR}/")
            break


if __name__ == "__main__":
    main()
