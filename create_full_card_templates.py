from pathlib import Path
import shutil

def create_full_card_templates():
    """
    Schneidet die Slots als Vollkarten-Templates und benennt sie nach den erwarteten Karten.
    """
    card_mapping = {
        "cardsample_1.jpg": [("a", "diamonds"), ("j", "diamonds"), ("5", "hearts")],
        "cardsample_2.jpg": [("8", "hearts"), ("2", "hearts"), ("2", "spades")],
        "cardsample_3.jpg": [("q", "clubs"), ("2", "hearts"), ("6", "clubs")],
        "cardsample_4.jpg": [("j", "diamonds"), ("10", "clubs"), ("k", "diamonds")],
        "cardsample_5.jpg": [("a", "spades"), ("6", "spades"), ("9", "diamonds")],
    }

    full_templates_dir = Path("templates/cards")
    full_templates_dir.mkdir(exist_ok=True)

    for sample, cards in card_mapping.items():
        sample_path = Path("templates/cards") / sample
        if not sample_path.exists():
            print(f"Sample {sample} not found")
            continue

        from PIL import Image
        img = Image.open(sample_path)
        width, height = img.size

        CARD_SLOTS = [
            (0.215, 0.375, 0.115, 0.20),
            (0.315, 0.375, 0.115, 0.20),
            (0.415, 0.375, 0.115, 0.20),
        ]

        for i, (rank, suit) in enumerate(cards):
            x_rel, y_rel, w_rel, h_rel = CARD_SLOTS[i]
            x = int(x_rel * width)
            y = int(y_rel * height)
            w = int(w_rel * width)
            h = int(h_rel * height)

            roi = img.crop((x, y, x + w, y + h))

            template_name = f"{rank}_{suit}.png"
            template_path = full_templates_dir / template_name
            roi.save(template_path)
            print(f"Saved full card template: {template_name}")

if __name__ == "__main__":
    create_full_card_templates()