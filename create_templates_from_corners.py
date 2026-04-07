from pathlib import Path
import shutil

def create_rank_suit_templates():
    """
    Erstellt Rank- und Suit-Templates basierend auf den User-Angaben.
    """
    ranks_dir = Path("templates/cards/ranks")
    suits_dir = Path("templates/cards/suits")

    # Mapping von Screenshot zu Karten
    card_mapping = {
        "cardsample_1.jpg": [("a", "diamonds"), ("j", "diamonds"), ("5", "hearts")],
        "cardsample_2.jpg": [("8", "hearts"), ("2", "hearts"), ("2", "spades")],
        "cardsample_3.jpg": [("q", "clubs"), ("2", "hearts"), ("6", "clubs")],
        "cardsample_4.jpg": [("j", "diamonds"), ("10", "clubs"), ("k", "diamonds")],
        "cardsample_5.jpg": [("a", "spades"), ("6", "spades"), ("9", "diamonds")],
    }

    used_ranks = set()
    used_suits = set()

    for sample, cards in card_mapping.items():
        sample_stem = Path(sample).stem  # z.B. "cardsample_1"
        for i, (rank, suit) in enumerate(cards, 1):
            corner_file = ranks_dir / f"{sample_stem}_card{i}_corner.png"
            if not corner_file.exists():
                print(f"Warnung: {corner_file} nicht gefunden")
                continue

            # Rank-Template
            if rank not in used_ranks:
                rank_target = ranks_dir / f"{rank}.png"
                shutil.copy(corner_file, rank_target)
                print(f"Rank-Template: {rank_target}")
                used_ranks.add(rank)

            # Suit-Template
            if suit not in used_suits:
                suit_target = suits_dir / f"{suit}.png"
                shutil.copy(corner_file, suit_target)
                print(f"Suit-Template: {suit_target}")
                used_suits.add(suit)

if __name__ == "__main__":
    create_rank_suit_templates()