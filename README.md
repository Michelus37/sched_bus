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

1. the current state  
2. the available actions  
3. the conditions for each outcome  
4. the transition to the next state  

This makes the system easier to test, maintain, and extend later.

## Project Goal

The final goal is to have a logical foundation that can be reused for things such as:

- simulation
- scripting
- automated decision-making
- further technical integration

## Notes

This repository focuses on **logic and structure first**.  
Implementation details, direct game interaction, and technical integration can be added later on top of this foundation.