import cv2
import numpy as np
from pathlib import Path

def analyze_card_samples():
    samples_dir = Path("templates/cards")
    for sample_path in sorted(samples_dir.glob("cardsample_*.jpg")):
        img = cv2.imread(str(sample_path))
        if img is None:
            print(f"{sample_path.name}: Failed to load")
            continue

        height, width = img.shape[:2]
        print(f"{sample_path.name}: {width}x{height}")

        # Simple card presence check: look for white rectangles
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        card_like = [c for c in contours if cv2.contourArea(c) > 10000]  # rough card size
        print(f"  Potential cards: {len(card_like)}")

if __name__ == "__main__":
    analyze_card_samples()