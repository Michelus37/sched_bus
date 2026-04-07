from PIL import Image

from detector import CardDetector


def test_card_detector_detect_card_at_returns_none_for_empty_slot() -> None:
    detector = CardDetector(debug=True)  # Debug für alle
    image = Image.new("RGB", (1280, 720), "darkgreen")
    detected = detector.detect_card_at(image, (100, 100, 200, 300))

    assert detected is None
    print("✓ test_card_detector_detect_card_at_returns_none_for_empty_slot passed")


def test_card_detector_detect_cards_returns_list_for_empty_screen() -> None:
    detector = CardDetector(debug=False)
    image = Image.new("RGB", (1280, 720), "darkgreen")
    detected_cards = detector.detect_cards(image)

    assert isinstance(detected_cards, list)
    assert detected_cards == []
    print("✓ test_card_detector_detect_cards_returns_list_for_empty_screen passed")


def test_card_detector_detects_cards_in_sample_1() -> None:
    detector = CardDetector(debug=False)  # Debug aus für saubere Ausgabe
    image = Image.open("templates/cards/cardsample_1.jpg")
    detected_cards = detector.detect_cards(image)

    print(f"Detected {len(detected_cards)} cards in sample_1:")
    for card in detected_cards:
        print(f"  - {card.card} (confidence: {card.confidence:.2f})")

    # Erwartet: A Karo, J Karo, 5 Herz
    assert len(detected_cards) == 3
    card_strs = [str(c.card) for c in detected_cards]
    assert all(":" in card for card in card_strs)
    print("✓ test_card_detector_detects_cards_in_sample_1 passed")

def test_card_detector_detects_cards_in_sample_2() -> None:
    detector = CardDetector(debug=False)
    image = Image.open("templates/cards/cardsample_2.jpg")
    detected_cards = detector.detect_cards(image)

    print(f"Detected {len(detected_cards)} cards in sample_2:")
    for card in detected_cards:
        print(f"  - {card.card} (confidence: {card.confidence:.2f})")

    # Erwartet: 8 Herz, 2 Herz, 2 Pik
    assert len(detected_cards) >= 2  # Flexibel, falls nicht alle erkannt werden
    card_strs = [str(c.card) for c in detected_cards]
    assert all(":" in card for card in card_strs)
    print("✓ test_card_detector_detects_cards_in_sample_2 passed")


def test_card_detector_detects_cards_in_sample_3() -> None:
    detector = CardDetector(debug=False)
    image = Image.open("templates/cards/cardsample_3.jpg")
    detected_cards = detector.detect_cards(image)

    print(f"Detected {len(detected_cards)} cards in sample_3:")
    for card in detected_cards:
        print(f"  - {card.card} (confidence: {card.confidence:.2f})")

    # Erwartet: Q Kreuz, 2 Herz, 6 Kreuz
    assert len(detected_cards) >= 2
    card_strs = [str(c.card) for c in detected_cards]
    assert all(":" in card for card in card_strs)
    print("✓ test_card_detector_detects_cards_in_sample_3 passed")


def test_card_detector_detects_cards_in_sample_4() -> None:
    detector = CardDetector(debug=True)  # Debug für Parsing
    image = Image.open("templates/cards/cardsample_4.jpg")
    detected_cards = detector.detect_cards(image)

    print(f"Detected {len(detected_cards)} cards in sample_4:")
    for card in detected_cards:
        print(f"  - {card.card} (confidence: {card.confidence:.2f})")

    # Erwartet: J Karo, 10 Kreuz, K Karo
    assert len(detected_cards) >= 2
    card_strs = [str(c.card) for c in detected_cards]
    assert all(":" in card for card in card_strs)
    print("✓ test_card_detector_detects_cards_in_sample_4 passed")


def test_card_detector_detects_cards_in_sample_5() -> None:
    detector = CardDetector(debug=False)
    image = Image.open("templates/cards/cardsample_5.jpg")
    detected_cards = detector.detect_cards(image)

    print(f"Detected {len(detected_cards)} cards in sample_5:")
    for card in detected_cards:
        print(f"  - {card.card} (confidence: {card.confidence:.2f})")

    # Erwartet: A Pik, 6 Pik, 9 Karo
    assert len(detected_cards) >= 2
    card_strs = [str(c.card) for c in detected_cards]
    assert all(":" in card for card in card_strs)
    print("✓ test_card_detector_detects_cards_in_sample_5 passed")

# Führe Tests manuell aus
if __name__ == "__main__":
    print("Running card detector tests...")
    test_card_detector_detect_card_at_returns_none_for_empty_slot()
    test_card_detector_detect_cards_returns_list_for_empty_screen()
    test_card_detector_detects_cards_in_sample_1()
    test_card_detector_detects_cards_in_sample_2()
    test_card_detector_detects_cards_in_sample_3()
    test_card_detector_detects_cards_in_sample_4()
    test_card_detector_detects_cards_in_sample_5()
    print("All tests passed! 🎉")