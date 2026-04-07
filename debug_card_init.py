#!/usr/bin/env python3
"""Debug card initialization."""

from models import Card, Rank, Suit

# Test 1: Create a card with valid values
print("Test 1: Valid card")
card1 = Card(rank=Rank.ACE, suit=Suit.DIAMONDS)
print(f"  Created: {card1}")
print(f"  String: {str(card1)}")

# Test 2: Create a card with None values
print("\nTest 2: Card with None values")
try:
    card2 = Card(rank=None, suit=None)
    print(f"  Created: {card2}")
    print(f"  String: {str(card2)}")
except Exception as e:
    print(f"  ERROR: {type(e).__name__}: {e}")

# Test 3: Create a card with partial None
print("\nTest 3: Card with partial None")
try:
    card3 = Card(rank=Rank.JACK, suit=None)
    print(f"  Created: {card3}")
    print(f"  String: {str(card3)}")
except Exception as e:
    print(f"  ERROR: {type(e).__name__}: {e}")

print("\nAll tests completed!")
