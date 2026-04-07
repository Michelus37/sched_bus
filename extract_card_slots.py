from PIL import Image
from pathlib import Path
import cv2
import numpy as np

def extract_card_slots_from_samples():
    """
    Schneidet die festen Kartenslots aus den cardsample_*.jpg aus und speichert sie als potenzielle Templates.
    Die Slots sind relativ: card1 (0.215, 0.375, 0.115, 0.20), etc.
    """
    samples_dir = Path("templates/cards")
    output_dir = samples_dir / "extracted_slots"
    output_dir.mkdir(exist_ok=True)

    CARD_SLOTS = [
        ("card1", 0.215, 0.375, 0.115, 0.20),
        ("card2", 0.315, 0.375, 0.115, 0.20),
        ("card3", 0.415, 0.375, 0.115, 0.20),
    ]

    for sample_path in sorted(samples_dir.glob("cardsample_*.jpg")):
        img = Image.open(sample_path)
        width, height = img.size

        for slot_name, x_rel, y_rel, w_rel, h_rel in CARD_SLOTS:
            x = int(x_rel * width)
            y = int(y_rel * height)
            w = int(w_rel * width)
            h = int(h_rel * height)

            roi = img.crop((x, y, x + w, y + h))

            # Speichere als PNG für bessere Qualität
            output_path = output_dir / f"{sample_path.stem}_{slot_name}.png"
            roi.save(output_path)
            print(f"Extracted {output_path}")

if __name__ == "__main__":
    extract_card_slots_from_samples()