# CLAUDE.md — Youth Soccer Lineup Generator

## Project overview
This is a mostly complete Python project that generates youth soccer lineups for 5v5 and 7v7 formats, surfaced as a Streamlit app. The core logic is stable. Work at this stage is refinement, bug fixes, and UI improvements — not rebuilds.

## Project structure
- `Home.py` — landing page for Streamlit - does very little beyond directing the user to the 5v5 and 7v7 lineup generators
- `pages/1_5v5_Generator.py` — 5v5 lineup generation logic, constraint enforcement, player assignment, and format UI
- `pages/2_7v7_Generator.py` — 7v7 lineup generation logic, constraint enforcement, player assignment, and format UI
- These files are self-contained — do not split or restructure them
  without explicit instruction

## Domain rules (do not change without explicit instruction)
The following constraints are built into each generator file. Never modify them unless I explicitly ask:

- Players must receive equal or near-equal playing time across the game
- Players must receive adequate rest breaks (no player should play continuously without a break)
- Players must play enough minutes to stay engaged (no player should sit for too long at a stretch)
- Players should be assigned to their preferred positions where possible
- Particularly strong players and particularly weak players should not be on the field together (to maintain balance)
- These rules apply separately for 5v5 and 7v7 formats, which may have different implementations
- For 5v5, a goalkeeper plays an entire quarter and this is treated as a single period of play for accounting
- For 7v7, a goalkeeper plays either a 10 or 15 minute block, and these minutes are the equivalent of 10 to 15 field minutes

## How to work with me

**Always explain before changing.**
Before modifying any existing code, describe what you plan to change and why. Wait for my confirmation before proceeding. This applies to refactors, bug fixes, and UI changes alike.

**Ask before assuming.**
If you are uncertain about how a rule is implemented, how a data structure works, or what I intend, stop and ask. Do not guess and proceed. A wrong assumption in this project can silently break lineup fairness logic in ways that are hard to detect.

**One change at a time.**
Propose and complete one logical change before moving to the next. Do not bundle multiple changes into a single edit unless I ask for it.

**Flag uncertainty explicitly.**
If you are not confident about something — a Python library's behavior, a Streamlit API detail, or how a constraint is enforced — say so clearly. "I'm not sure how X works here, can you confirm?" is always the right move.

## Code style preferences
- Prefer clear, readable code over clever one-liners — this project may be maintained by someone other than the original author
- Add a brief comment when implementing or modifying any constraint-related logic so the intent is clear

## What not to do
- Do not refactor working code without being asked
- Do not change constraint logic to "simplify" it without fully understanding the rule it enforces
- Do not add new dependencies without flagging them first
