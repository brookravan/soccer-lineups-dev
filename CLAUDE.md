# CLAUDE.md — Youth Soccer Lineup Generator

## Project overview
This is a mostly complete Python project that generates youth soccer lineups for 5v5 and 7v7 formats, surfaced as a Streamlit app. The core logic is stable. Work at this stage is refinement, bug fixes, and UI improvements — not rebuilds.

## Project structure
- `Home.py` — Streamlit landing page, pure UI only, no logic. Do not add logic here.
- `shared_logic.py` — shared lineup generation logic, constraint enforcement, and utilities used by both generator pages. Lives in project root for clean importing.
- `pages/1_5v5_Generator.py` — 5v5-specific logic, player selection, and Streamlit UI. Imports shared logic from `shared_logic.py`.
- `pages/2_7v7_Generator.py` — 7v7-specific logic, player selection, and Streamlit UI. Imports shared logic from `shared_logic.py`.

**Structure rules**
- Logic that applies to both formats belongs in `shared_logic.py`
- Logic that is format-specific stays in the relevant generator file
- When adding new functionality, explicitly decide which category it belongs to before writing any code — ask if unsure
- Do not put utility logic in `Home.py` or in the `pages/` folder outside the generator files
- When a bug is found in shared logic, fix it once in `shared_logic.py` — do not patch it separately in each generator file

**Refactor sequencing**
- When refactoring, always extract shared logic first and verify both generator files work correctly before fixing bugs
- Fix bugs after the refactor is confirmed working — never refactor and fix bugs in the same pass

## Game structure

**5v5 format**
- 4 quarters of 10 minutes each
- Each quarter is split into 2 substitution periods
- Results in 8 substitution periods per game
- Goalkeepers play one full quarter each
- Formations are defined in `FORMATION_CONFIGS` and follow soccer convention: defense|midfield|forwards with goalkeeper implied (e.g. 2-2-0 = 2 defenders, 2 midfielders, 0 forwards, plus goalkeeper)
- Available 5v5 formations: `2-2-0` and `1-2-1`

**7v7 format**
- 2 halves of 25 minutes each
- Substitutions occur at the 10, 15, and 20 minute mark of each half
- Results in 4 substitution periods per half, 8 total per game
- Goalkeepers play either a 15-minute or 10-minute shift per half (2 shifts per half) — the split can vary
- Formations are defined in `FORMATION_CONFIGS` using the same defense|midfield|forwards convention
- Available 7v7 formations: `3-2-1`, `3-1-2`, `2-2-2`, `2-3-1`, `2-1-3`

**Goalkeeper rules (both formats)**
- Goalkeeper playing time is predetermined and fixed
- Do not flag goalkeeper playing time as a fairness imbalance
- Goalkeepers are excluded from split_pairs and synergy_pairs logic entirely

**5v5 candidate selection sort order**
Within `generate_rotation`, field player candidates are sorted by `(part_score[p], not sat_last[p], con_played[p] >= 2)` — ascending, so lowest values get highest priority:
1. `part_score` — fewest participation credits first (primary, equal time is top priority)
2. `not sat_last` — among ties, recently-rested players get priority (False sorts before True)
3. `con_played >= 2` — consecutive-play limit as final tiebreaker

**6-player edge case (5v5)**
With exactly 6 attending players, the math works out to exactly 6 participation credits per player (36 total ÷ 6 players). The algorithm is designed to achieve this:
- Players who served as GK for a quarter (1 credit) should sit exactly 1 field block in the remaining 6 blocks → 5 field + 1 GK = 6 total
- Players who never play GK should sit exactly 2 field blocks across 8 blocks → 6 field = 6 total
The `part_score` sort key is what makes this work — without it, GK players appear falsely caught up because `total_played` counts their 2 GK blocks as 2 credits instead of 1.

## Key variables

**`roster_raw`** — the full team roster. All players on the team regardless of attendance.

**`player_ranks`** — a 3-digit number per player indicating position preference in defense|midfield|forward order. Example: 213 = prefers midfield, then defense, then forward. 132 = prefers defense, then forward, then midfield.

**Attending players** — a subset of `roster_raw` selected via checkboxes in the Streamlit UI for each specific game. All lineup generation must use only this subset.

**`split_pairs`** — two players who should not occupy non-goalkeeper positions in the same period. Used either because both are strong (spread their impact across periods) or both are weak (avoid periods where the team is uncompetitive). Honored only when playing time remains balanced — playing time takes priority.

**`synergy_pairs`** — two players who should be on the field together whenever possible. Lower priority than playing time and split_pairs.

**`FORMATION_CONFIGS`** — defines available formations for each format. Do not modify without explicit instruction.

**`part_score`** (5v5 only, internal to `generate_rotation`) — tracks participation credits the same way the display table does: GK earns 1 credit for the whole quarter (credited on the first block only), field players earn 1 credit per block. This is the primary sort key for candidate selection — do not replace it with `total_played`, which counts every block equally and incorrectly overstates GK players' credit after their quarter. The 7v7 equivalent is `total_mins`, which already works correctly there.

**Random seed** — included in lineup generation so coaches can recreate a specific lineup by re-entering the same seed, especially when combined with a saved JSON settings file.

## Constraint priority order
When constraints conflict, resolve in this order (highest to lowest):
1. Equal or near-equal playing time for all field players
2. Honoring split_pairs (keep these players in separate periods when possible)
3. Honoring position preferences via player_ranks
4. Honoring synergy_pairs (keep these players together when possible)

## Manual overrides
- Coaches can manually override any programmatic lineup suggestion via the Streamlit UI
- Manual overrides are the final step and supersede all constraints and rules
- After a manual override, the only automatic update that should occur is recalculation of the playing time table to reflect the changes
- Do not attempt to re-apply constraints after a manual override

## Persistent settings (JSON)
- All settings can be saved to a local JSON file via a Streamlit download button and reloaded in a future session
- The JSON saves: full roster and player_ranks, split_pairs, synergy_pairs, attending players, formation configs, and the random seed
- This exists because re-entering all preferences each session is not practical — do not suggest workflows that require users to re-enter settings manually

## Display components (do not modify without explicit instruction)
- **mplsoccer + matplotlib** — renders a matrix of soccer fields showing player positions per period, with labels for substitutions and bench players. This is working correctly — do not touch it unless explicitly asked.
- **Playing time table** — displayed at the bottom, shows each player's periods played (5v5) or minutes played (7v7). Must always reflect the final lineup including any manual overrides.

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
- Do not modify the mplsoccer display without being asked
- Do not suggest re-entering settings that are already handled by the JSON save/load system
