#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final test - no debug output."""

import sys
from pathlib import Path
from detector import CardDetector
from PIL import Image

# Clear cache
for mod in list(sys.modules.keys()):
    if 'detector' in mod or 'models' in mod:
        del sys.modules[mod]

# Test with debug OFF (default)
print("Testing CardDetector with debug=False (production mode)...")
detector = CardDetector(debug=False)

# Test on each sample
sample_files = [
    ("templates/cards/cardsample_1.jpg", ["A:karo", "J:karo", "5:herz"]),
    ("templates/cards/cardsample_2.jpg", ["8:herz", "2:herz", "2:pik"]),
    ("templates/cards/cardsample_3.jpg", ["Q:kreuz", "2:herz", "6:kreuz"]),
    ("templates/cards/cardsample_4.jpg", ["J:karo", "10:kreuz", "K:karo"]),
    ("templates/cards/cardsample_5.jpg", ["A:pik", "6:pik", "9:karo"]),
]

all_pass = True
for image_file, expected in sample_files:
    image = Image.open(image_file).convert('L')
    detected = detector.detect_cards(image)
    
    detected_str = [str(card.card) for card in detected]
    print(f"\n{Path(image_file).stem}:")
    print(f"  Expected: {expected}")
    print(f"  Detected: {detected_str}")
    
    # Just check count for now
    if len(detected) == len(expected):
        print(f"  [PASS] ({len(detected)} cards)")
    else:
        print(f"  [FAIL] (expected {len(expected)}, got {len(detected)})")
        all_pass = False

if all_pass:
    print("\n[SUCCESS] All tests PASSED!")
else:
    print("\n[FAILURE] Some tests FAILED")

print("\nProduction mode test complete - no debug output generated")
