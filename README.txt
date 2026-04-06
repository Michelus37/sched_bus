Struktur:

- models.py      -> Datamodelle, Enums, RoundContext
- deck.py        -> Deck-Erzeugung, Shuffle, Draw
- rules.py       -> Reine Auswertungslogik für die 4 Schritte
- strategy.py    -> Strategy-Interface + RandomStrategy
- engine.py      -> State Machine / Ablaufsteuerung
- simulation.py  -> Viele Runden simulieren
- main.py        -> Einfacher Demo-Einstieg

Start:
    python main.py

Wichtige Regelentscheidungen:
- Schritt 2: Gleichstand ist weder höher noch tiefer -> immer verloren
- Schritt 3: "innerhalb" ist inklusive Grenzen
- Schritt 3: Grenzen werden immer mit min/max aus Karte 1 und 2 bestimmt
- Schritt 3: Bei gleichen ersten beiden Karten ist nur exakt derselbe Wert "innerhalb"
