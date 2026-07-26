# Roster data

Each `games/{id}/characters.json` file is an array sorted by `name.casefold()`.

```json
{
  "name": "Character Name",
  "guest": false,
  "orbment": [
    {"elemental": null, "line": 0},
    {"elemental": "time", "line": 1}
  ]
}
```

- `guest` is always a boolean. Guest characters are hidden until the planner's checkbox is enabled.
- `elemental` is `null` or one of `earth`, `water`, `fire`, `wind`, `time`, `space`, `mirage`.
- `line` is an integer. Positive values define arts-evaluation lines; `0` and negative values contribute to every positive line.
- Slot count and line topology are title- and character-specific hand-maintained data. Verify them from an authoritative source before editing.
- The planner renders every slot in the array; it supports six-slot FC and seven-slot later rosters without a fixed count.
