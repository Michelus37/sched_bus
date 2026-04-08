# sched_bus

> **Completely vibe-coded.** This project was built entirely through conversations with Claude — no manual architecture planning, no upfront design docs. Just vibes and iterations.

A live automation bot for the **Ride the Bus** minigame in **Schedule I**. It watches the game screen, detects the current state and visible cards, picks the statistically best move using a heuristic strategy, and clicks the right button — fully automatically.

## How it works

```
┌──────────────────────────────────────────────┐
│  Game Loop                                   │
├──────────────────────────────────────────────┤
│ 1. Find game window on screen                │
│ 2. Capture screenshot of game content        │
│ 3. Detect UI state (which panel is visible?) │
│ 4. Detect cards on the table                 │
│ 5. Strategy picks the best move              │
│ 6. Click the button                          │
│ 7. Wait 4 seconds, repeat                    │
└──────────────────────────────────────────────┘
```

The game has four decision steps per round:

| Step | Decision | Cards visible |
|------|----------|---------------|
| 1 | Red or Black? | 0 |
| 2 | Higher or Lower? | 1 |
| 3 | Inside or Outside? | 2 |
| 4 | Which suit? | 3 |

The strategy tracks which cards have been revealed and uses the remaining deck to calculate the highest-probability choice at each step.

## Setup

### Requirements

- Python 3.11+
- Schedule I running in **windowed mode at 1920×1080**
- The game window can be placed anywhere on screen — the bot finds it automatically by window title

### Install dependencies

```bash
pip install pillow opencv-python pyautogui pygetwindow
```

### Window configuration

The bot requires the game to run at exactly **1920×1080** in windowed mode. All card slot positions and button coordinates are calibrated to this resolution.

1. Launch **Schedule I**
2. In the game settings, set the resolution to **1920×1080** and mode to **Windowed**
3. You do not need to place the window in a specific position — the bot detects it by the window title `Schedule I`

### Card templates

The bot recognises cards by matching the top-left corner of each card against template images in `templates/cards_new/`. The more templates you have, the better the card detection.

To collect templates while playing:

```bash
python capture_templates.py
```

Play normally — every time a card appears that the bot doesn't recognise yet, a corner crop is saved to `templates/cards_new/` as `_capture_NNNN_card1.png`. Rename the file to the correct card name (e.g. `K_hearts.png`, `7_spades.png`, `Q_karo.png`) and it will be picked up automatically next run.

Supported filename formats: `RANK_SUIT.png` — variant images like `K_hearts_2.png` are also supported for cards with multiple visual states.

## Running the bot

```bash
python game_loop.py
```

Make sure the game is open and on the Ride the Bus table before starting. The bot will print its state, action, decision and detected cards to the console on every tick:

```
state=WAIT_READY                   action=CLICK_READY        decision=-          cards=[none]
state=WAIT_COLOR_DECISION          action=CHOOSE_COLOR        decision=BLACK      cards=[none]
state=WAIT_HIGHER_LOWER_DECISION   action=CHOOSE_HIGHER_LOWER decision=HIGHER     cards=[ACE:karo]
state=WAIT_INSIDE_OUTSIDE_DECISION action=CHOOSE_INSIDE_OUTSIDE decision=OUTSIDE  cards=[ACE:karo, JACK:karo]
state=WAIT_SUIT_DECISION           action=CHOOSE_SUIT         decision=HEARTS     cards=[ACE:karo, JACK:karo, FIVE:herz]
```

Stop with **Ctrl+C**.

## Project structure

```
game_loop.py          — main entry point, runs the automation loop
live_adapter.py       — bridges UI state to strategy decisions
clicker.py            — translates decisions into mouse clicks
detector.py           — button and card detection via OpenCV template matching
game_reader.py        — captures screenshot and assembles a game snapshot
vision.py             — screenshot capture and window detection
strategy.py           — decision strategies (heuristic, lookahead, random)
capture_templates.py  — helper to collect new card templates during play

models.py             — core data models and enums
deck.py               — deck creation and shuffling
rules.py              — pure rule evaluation for all four game steps
engine.py             — round state machine (used for simulation)
simulation.py         — multi-round simulation and statistics
main.py               — run simulations offline

templates/
  buttons/            — panel and button reference images
  cards_new/          — card corner templates for recognition

screens/              — reference screenshots used during development
tests/                — unit tests for game logic
```
