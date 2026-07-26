---
name: add-trails-character
description: Add, correct, or reclassify playable and guest characters in this Trails orbment planner. Use when changing a game's characters.json roster, guest visibility, orbment slot restrictions, or line topology.
---

# Add Trails Character

Edit only the target game's `characters.json` unless the requested roster behavior requires a UI change.

1. Read [the roster reference](references/roster-data.md).
2. Confirm the game id and the authoritative slot layout before editing; do not infer it from another title.
3. Add or update `name`, explicit `guest`, and every orbment slot. Keep entries alphabetized by case-insensitive name.
4. Run `python3 scripts/validate_trails_game_data.py --game GAME_ID`.
5. If guest behavior or game registration changed, preview with `python3 -m http.server` and confirm the character appears or hides correctly.

Do not run `--resort-json-only` for a one-character edit unless rewriting every game is intended.
