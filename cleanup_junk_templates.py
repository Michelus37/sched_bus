from pathlib import Path
import os

ranks_dir = Path("templates/cards/ranks")

# Find and delete junk files (corners from corner extraction script)
junk_files = [f for f in ranks_dir.glob("cardsample_*_corner.png")]

print(f"Found {len(junk_files)} junk files to delete:")
for f in junk_files:
    print(f"  - {f.name}")
    os.remove(f)

print(f"Deleted {len(junk_files)} files")

# Also check suits directory
suits_dir = Path("templates/cards/suits")
junk_files_suits = [f for f in suits_dir.glob("cardsample_*_corner.png")]
print(f"\nFound {len(junk_files_suits)} junk files in suits:")
for f in junk_files_suits:
    print(f"  - {f.name}")
    os.remove(f)

print(f"Deleted {len(junk_files_suits)} files")

print("\nCleanup complete!")
