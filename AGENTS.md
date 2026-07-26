# Trails Tools Contributor Guide

This is a static vanilla HTML, JavaScript, and CSS orbment planner. `orbment-planner.html` hosts the UI; `app.js` loads data using relative `games/{id}/...` URLs, which must remain GitHub Pages-compatible.

## Use the project skills

- Use `$add-trails-character` for roster, guest, orbment-slot, and line-topology edits.
- Use `$maintain-trails-game-data` for new titles and wiki-derived arts/quartz work.
- Use `$validate-trails-game-data` after data, importer, selector, or planner changes.

## Data and maintenance

Each game directory has `characters.json`, `quartz.json`, and `arts.json`. Character rosters are hand-maintained. The wiki importer updates arts and quartz from cached MediaWiki responses only.

Run `python3 scripts/validate_trails_game_data.py` after changes. `python3 scripts/build_trails_wiki_data.py --resort-json-only` and `--reassign-quartz-types-only` rewrite every discovered game data set; use them only when that broad rewrite is intended.

For browser checks, run `python3 -m http.server` from the repository root; do not open the planner with `file://`.
