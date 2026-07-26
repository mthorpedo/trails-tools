---
name: validate-trails-game-data
description: Validate Trails orbment planner game data and registration. Use after changing character, quartz, art, importer, or game-selector data, and for validation-only requests.
---

# Validate Trails Game Data

Run the validator from the repository root:

```bash
python3 scripts/validate_trails_game_data.py
python3 scripts/validate_trails_game_data.py --game GAME_ID
```

Read [the validation contract](references/validation.md) when interpreting failures or extending the checker. Fix data at the reported path; do not use the validator as a formatter.

After a change to game registration or planner code, also serve the root with `python3 -m http.server` and verify game loading, character selection, quartz assignment, line totals, and enabled arts.
