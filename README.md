# sched_bus

This project is a structured analysis of a minigame from **Schedule I**, with the goal of turning its flow into a clean and reusable logical model.

Instead of building a messy collection of `if` statements, the project focuses on describing the minigame as a set of:

- **states**
- **rules**
- **transitions**
- **success conditions**
- **failure conditions**
- **special cases**

The idea is to make the logic easy to understand first, and only then prepare it for technical use in code.

## Purpose

The main purpose of this repository is to break the minigame down into a form that can later be implemented in Python or another language without depending on the original game code directly.

This means the project is not just about automation, but about building a **clear decision model** of how the minigame works.

## Approach

The logic is modeled in a structured way, similar to a:

- **state machine**
- **decision tree**
- or a combination of both

Each step of the minigame is described by:

┌─────────────────────────────────────────────┐
│  Game Loop (every 2 seconds)               │
├─────────────────────────────────────────────┤
│ 1. Screenshot capture (whole screen)        │
│ 2. Detect game state (which of 5 screens?)  │
│ 3. Crop card region + detect cards          │
│ 4. Feed cards to strategy.decide()          │
│ 5. Get action (which button to click)       │
│ 6. Execute mouse click                      │
│ 7. Wait 2 seconds, repeat                   │
└─────────────────────────────────────────────┘

This makes the system easier to test, maintain, and extend later.

## Project Goal

The final goal is to have a logical foundation that can be reused for things such as:

- simulation
- scripting
- automated decision-making
- further technical integration

## Project Structure

- `models.py` → core data models, enums, and round context
- `deck.py` → deck creation, shuffling, and card drawing
- `rules.py` → pure rule evaluation for all four game steps
- `strategy.py` → strategy interface and strategy implementations
- `engine.py` → round flow and state machine logic
- `simulation.py` → repeated round simulation and statistics
- `main.py` → simple entry point for demo runs and simulations
- `tests/` → automated tests for rules and engine behavior

## Running the Project

You can run the project directly with:

```bash
python main.py