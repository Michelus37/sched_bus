#!/usr/bin/env python3
"""Debug card initialization with traceback."""

import traceback
from models import Card, Rank, Suit

# Test 2: Create a card with None values
print("Test 2: Card with None values - with traceback")
try:
    card2 = Card(rank=None, suit=None)
    print(f"  Created: {card2}")
    print(f"  String: {str(card2)}")
except Exception as e:
    print(f"  ERROR: {type(e).__name__}: {e}")
    traceback.print_exc()

print("\nDone!")
