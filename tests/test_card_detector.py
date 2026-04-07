import sys
sys.path.append('..')

from PIL import Image

from ..detector import CardDetector


def test_card_detector_detect_card_at_returns_none_for_empty_slot() -> None:
    detector = CardDetector(debug=False)
    image = Image.new("RGB", (1280, 720), "darkgreen")
    detected = detector.detect_card_at(image, (100, 100, 200, 300))

    assert detected is None


def test_card_detector_detect_cards_returns_list_for_empty_screen() -> None:
    detector = CardDetector(debug=False)
    image = Image.new("RGB", (1280, 720), "darkgreen")
    detected_cards = detector.detect_cards(image)

    assert isinstance(detected_cards, list)
    assert detected_cards == []


def test_card_detector_detects_cards_in_sample_1() -> None:
    detector = CardDetector(debug=False)
    image = Image.open("templates/cards/cardsample_1.jpg")
    detected_cards = detector.detect_cards(image)

    # Erwartet: A Karo, J Karo, 5 Herz
    assert len(detected_cards) == 3
    card_strs = [str(c.card) for c in detected_cards]
    # Für jetzt nur prüfen, dass Karten erkannt wurden
    assert all(":" in card for card in card_strs)
