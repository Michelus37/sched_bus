from PIL import Image
from pathlib import Path

def extract_rank_suit_from_slots():
    """
    Schneidet Rank und Suit aus den extrahierten Slots.
    Rank: obere linke Ecke (ca. 30% Breite, 20% Höhe)
    Suit: daneben oder darunter, aber für Einfachheit nehmen wir die Ecke für beide.
    """
    slots_dir = Path("templates/cards/extracted_slots")
    ranks_dir = Path("templates/cards/ranks")
    suits_dir = Path("templates/cards/suits")
    ranks_dir.mkdir(exist_ok=True)
    suits_dir.mkdir(exist_ok=True)

    for slot_path in sorted(slots_dir.glob("*.png")):
        img = Image.open(slot_path)
        width, height = img.size

        # Rank/Suit Ecke: obere linke 30% x 20%
        corner_width = int(width * 0.32)
        corner_height = int(height * 0.24)
        corner = img.crop((0, 0, corner_width, corner_height))

        # Für jetzt speichere ich die Ecke als potenzielles Template
        # Der User muss sie später umbenennen, z.B. zu "a.png" für Ace, "hearts.png" für Herz
        output_name = f"{slot_path.stem}_corner.png"
        corner.save(ranks_dir / output_name)  # Erstmal in ranks, User kann verschieben
        print(f"Extracted corner: {output_name}")

if __name__ == "__main__":
    extract_rank_suit_from_slots()