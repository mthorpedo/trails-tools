# Validation contract

The validator is read-only and discovers every directory under `games/`.

- Each game directory has `characters.json`, `quartz.json`, and `arts.json`, all JSON arrays.
- Every game directory appears exactly once in `orbment-planner.html`'s `#game` selector; no selector option may point to a missing directory.
- Character names are unique and case-insensitively sorted. Characters have boolean `guest` and non-empty `orbment` arrays.
- Quartz and arts use canonical element names and maps with exactly earth, water, fire, wind, time, space, and mirage. Values are non-negative integers.
- Quartz names may repeat when the wiki has distinct rows with the same display name; their positive `type` values are dense from `1` through the maximum.
- Empty top-level arrays are allowed for a newly initialized title.

The validator deliberately does not decide whether roster slot layouts or wiki facts are accurate; check those against authoritative game/source material.
