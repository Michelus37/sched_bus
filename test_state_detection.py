from __future__ import annotations

from pathlib import Path

from detector import LiveUIState


TEST_IMAGES = {
    "1rdy.jpg": LiveUIState.WAIT_READY,
    "2red_black.jpg": LiveUIState.WAIT_COLOR_DECISION,
    "3higher_lower.jpg": LiveUIState.WAIT_HIGHER_LOWER_DECISION,
    "4inside_outside.jpg": LiveUIState.WAIT_INSIDE_OUTSIDE_DECISION,
    "5color.jpg": LiveUIState.WAIT_SUIT_DECISION,
}


class FilenameBasedStateDetector:
    """Temporary test detector.

    This is NOT real image recognition.
    It only maps known test screenshot filenames to expected UI states.

    Purpose:
    - verify your state model
    - verify your test setup
    - verify your later adapter flow
    """

    def detect_ui_state_from_path(self, image_path: str | Path) -> LiveUIState:
        image_path = Path(image_path)
        name = image_path.name.lower()

        if name in TEST_IMAGES:
            return TEST_IMAGES[name]

        return LiveUIState.UNKNOWN


def main() -> None:
    detector = FilenameBasedStateDetector()

    base_dir = Path(".")

    print("Testing screenshot state mapping...\n")

    success_count = 0
    total_count = 0

    for filename, expected_state in TEST_IMAGES.items():
        total_count += 1
        image_path = base_dir / "screens" / filename

        if not image_path.exists():
            print(f"[MISSING] {filename}")
            continue

        detected_state = detector.detect_ui_state_from_path(image_path)
        ok = detected_state == expected_state

        if ok:
            success_count += 1

        print(
            f"{filename:20} | expected={expected_state.name:30} "
            f"| detected={detected_state.name:30} | ok={ok}"
        )

    print("\nSummary:")
    print(f"Passed: {success_count}/{total_count}")


if __name__ == "__main__":
    main()