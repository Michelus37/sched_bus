#!/usr/bin/env python3
"""Fresh import test."""

import sys
import importlib

# Clear any cached modules
for mod in list(sys.modules.keys()):
    if 'models' in mod or 'detector' in mod:
        del sys.modules[mod]

# Now import fresh
from models import Card, Rank, Suit

print("Testing Card with None values:")
card = Card(rank=None, suit=None)
print(f"Card created: {type(card)}")
print(f"Card.rank: {card.rank}")
print(f"Card.suit: {card.suit}")
print(f"Calling str()...")
try:
    s = str(card)
    print(f"Result: {s}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

