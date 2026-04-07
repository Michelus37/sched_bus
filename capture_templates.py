"""
Template capture helper.

Run this alongside the game to automatically save card corner crops.
Each time a card appears in a slot, the top-left corner is saved as:
    templates/cards_new/_capture_NNNN.png

Rename the files afterwards to the correct card name, e.g.:
    K_hearts.png
    7_spades.png
    Q_diamonds.png   (or Q_karo.png — both work)

Controls:
    Press Ctrl+C to stop.
"""

from __future__ import annotations

import time
from pathlib import Path

from detector import CardDetector, ButtonDetector, StateDetector, LiveUIState
from game_reader import GameReader, TableLayout
from vision import PILScreenCapture, Region, find_game_window

SAVE_DIR = Path("templates/cards_new")
CORNER_W_FRAC = 0.42
CORNER_H_FRAC = 0.42
CARD_Y      = 422
CARD_W      = 145
CARD_H      = 195

_counter = [0]
_seen: set[str] = set()


def _save_corner(roi, slot_name: str, card_detector: CardDetector) -> None:
    if not hasattr(roi, "size"):
        return

    # Check if we already have a template for this card
    detected = card_detector.detect_card_at(roi, (0, 0, roi.size[0], roi.size[1]))
    if detected is not None:
        print(f"  [{slot_name}] already known: {detected.card} (score={detected.confidence:.2f}) — skipping")
        return

    w, h = roi.size
    corner = roi.crop((0, 0, int(w * CORNER_W_FRAC), int(h * CORNER_H_FRAC)))

    path = SAVE_DIR / f"_capture_{_counter[0]:04d}_{slot_name}.png"
    corner.save(path)
    print(f"  [{slot_name}] unknown card — saved {path.name}  (rename to e.g. K_hearts.png)")
    _counter[0] += 1


def main() -> None:
    print("Looking for game window...")
    window = find_game_window("Schedule I")
    print(f"Found: {window}")

    capture = PILScreenCapture(monitor_region=window)
    layout = TableLayout(
        table_region=Region(0, 0, 1920, 1080),
        card1_region=Region(290, CARD_Y, CARD_W, CARD_H),
        card2_region=Region(435, CARD_Y, CARD_W, CARD_H),
        card3_region=Region(580, CARD_Y, CARD_W, CARD_H),
        card4_region=Region(725, CARD_Y, CARD_W, CARD_H),
    )
    reader = GameReader(
        capture=capture,
        layout=layout,
        card_detector=CardDetector(debug=False),
        button_detector=ButtonDetector(debug=False),
        state_detector=StateDetector(),
    )

    # States where cards are newly revealed
    card_states = {
        LiveUIState.WAIT_HIGHER_LOWER_DECISION:   [("card1", layout.card1_region)],
        LiveUIState.WAIT_INSIDE_OUTSIDE_DECISION: [("card2", layout.card2_region)],
        LiveUIState.WAIT_SUIT_DECISION:           [("card3", layout.card3_region)],
    }

    last_state = LiveUIState.UNKNOWN
    print("Running — play the game normally, corner crops will be saved automatically.")
    print("Press Ctrl+C to stop.\n")

    while True:
        try:
            snapshot = reader.read_snapshot()
            state = snapshot.ui_state

            if state != last_state and state in card_states:
                table_img = capture.capture_region(layout.table_region)
                for slot_name, region in card_states[state]:
                    key = f"{state.name}_{slot_name}"
                    if key not in _seen:
                        roi = table_img.crop((
                            region.x, region.y,
                            region.x + region.width,
                            region.y + region.height,
                        ))
                        _save_corner(roi, slot_name, reader.card_detector)
                        _seen.add(key)

            if state != last_state:
                last_state = state
                _seen.clear()

            time.sleep(0.5)

        except KeyboardInterrupt:
            print(f"\nDone. Saved {_counter[0]} crops to {SAVE_DIR}/")
            break


if __name__ == "__main__":
    main()
