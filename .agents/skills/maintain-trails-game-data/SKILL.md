---
name: maintain-trails-game-data
description: Add a Trails title or import and refresh its arts and quartz data in this orbment planner. Use when creating games/{id}, registering a game, fetching MediaWiki parse data, adapting the importer to a wiki table, or maintaining quartz type rules.
---

# Maintain Trails Game Data

Read [the data-import reference](references/wiki-data.md) before changing source, parser, or quartz rules.

For a new game:

1. Create `games/{id}/` with all three JSON arrays, add one matching option to `#game` in `orbment-planner.html`, and validate registration.
2. Add cached arts/quartz input paths to `GAME_INPUTS` only when the title will use the wiki importer.
3. Inspect the source table headers and rows before reusing the FC or SC quartz parser. Add a parser variant when the layout differs.
4. Run the importer, inspect output counts and representative rows, then run the validator.

For existing wiki data, refresh the cached MediaWiki responses, run `python3 scripts/build_trails_wiki_data.py GAME_ID`, and validate the affected game. Run `--reassign-quartz-types-only` only after altering exclusivity rules; it rewrites all discovered game quartz files.
