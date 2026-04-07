from __future__ import annotations

from pathlib import Path
from PIL import Image

from detector import ButtonDetector


def main() -> None:
    screens_dir = Path("screens")
    detector = ButtonDetector(template_dir="templates/buttons")

    test_files = [
        "1rdy.jpg",
        "2red_black.jpg",
        "3higher_lower.jpg",
        "4inside_outside.jpg",
        "5color.jpg"
    ]

    for filename in test_files:
        image_path = screens_dir / filename

        if not image_path.exists():
            print(f"[MISSING] {image_path}")
            continue

        image = Image.open(image_path).convert("RGB")
        result = detector.detect_buttons(image)

        print(f"\n=== {filename} ===")
        print(f"ready_visible   : {result.ready_visible}")
        print(f"red_visible     : {result.red_visible}")
        print(f"black_visible   : {result.black_visible}")
        #print(f"forfeit_visible : {result.forfeit_visible}")
        print(f"higher_visible : {result.higher_visible}")
        print(f"lower_visible : {result.lower_visible}")
        print(f"inside_visible : {result.inside_visible}")
        print(f"outside_visible : {result.outside_visible}")
        print(f"heart_visible : {result.hearts_visible}")
        print(f"clubs_visible : {result.clubs_visible}")
        print(f"diamonds_visible : {result.diamonds_visible}")
        print(f"spades_visible : {result.spades_visible}")
        detector = ButtonDetector(template_dir="templates/buttons", debug=False)

if __name__ == "__main__":
    main()