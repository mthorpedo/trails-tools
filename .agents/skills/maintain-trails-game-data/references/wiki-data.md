# Wiki-backed game data

Each title directory contains `characters.json`, `quartz.json`, and `arts.json`. The importer writes only arts and quartz; character rosters are hand-maintained.

## MediaWiki import

Cache `action=parse&prop=text&format=json` responses outside the repository, then run:

```bash
python3 scripts/build_trails_wiki_data.py GAME_ID
```

`GAME_INPUTS` in the script is the configured source of cache paths. Inspect new wiki table headers before importing: FC-style quartz tables use six body columns, while SC-style tables use seven with an ignored slot-upgrade column.

## Data shapes

- Quartz: `name`, positive integer `type`, canonical `elemental`, seven-element integer `cost`, `effect`, and `level`.
- Arts: `name`, `description`, canonical `elemental`, seven-element `elemental-value`, EP `cost`, `time.cast`, `time.delay`, `power`, and `target-effect`.

Quartz `type` models in-loadout exclusivity. Tiered names share a type; status quartz, Effort/Prankster, gem aliases, and Carnage have intentional aliases in `build_trails_wiki_data.py`. Preserve those rules and compact resulting ids to `1..N`.

Wiki prose may be CC-BY-SA. Preserve appropriate Fandom attribution when copying prose verbatim.
