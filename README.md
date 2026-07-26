# Trails orbment planner

[![GitHub stars](https://img.shields.io/github/stars/mthorpedo/trails-tools?style=flat-square&logo=github)](https://github.com/mthorpedo/trails-tools/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

Static **HTML**, **JavaScript**, and **CSS** orbment planner for several *Trails* / *Kiseki* titles. Per-game data lives under [`games/`](games/) as `characters.json`, `quartz.json`, and `arts.json`.

## Tools and how to use them

### Orbment planner (hosted)

Choose a **game** and **character**. Assign quartz to slots, inspect **line sepith totals**, and see **enabled arts** for the current loadout.

### Wiki data build / maintenance

[`scripts/build_trails_wiki_data.py`](scripts/build_trails_wiki_data.py) refreshes **`arts.json`** and **`quartz.json`** from cached Fandom wiki HTML (not needed to simply use the hosted planner).

- **Regenerate** for a title: cache MediaWiki `action=parse` JSON at the paths listed in `GAME_INPUTS` inside the script, then run for example:
  - `python3 scripts/build_trails_wiki_data.py sky-fc` | `sky-sc` | `sky-tc` | `zero`
- **`--resort-json-only`** — Re-sort `arts.json`, `quartz.json`, and `characters.json` under each `games/*/` without fetching the wiki.
- **`--reassign-quartz-types-only`** — Recompute quartz **`type`** ids from the script’s rules for every `games/*/quartz.json`.

**Dependencies:** Python 3 and **BeautifulSoup** (the script prepends [`.build_deps/`](.build_deps/) to `sys.path`). Project-local Agent skills under [`.agent/skills/`](.agent/skills/) contain maintenance workflows and source-mapping guidance.

## Contributing

For development and local checks (not required for GitHub Pages visitors):

- **Local preview:** Browsers block `fetch()` on `file://`. Clone the repo, run a static HTTP server at the **project root** (for example `python3 -m http.server`), and open `http://localhost:PORT/` so relative `games/...` URLs resolve.
- **Workflow:** Branch from `main`. After changing wiki import logic or Fandom pages, refresh cached responses, run `build_trails_wiki_data.py` for the affected game id, then run `python3 scripts/validate_trails_game_data.py`. Use `--reassign-quartz-types-only` or `--resort-json-only` only when you intend those rewrites.

Pull requests are welcome once the repository is public; use GitHub **Issues** for the same `OWNER/REPO` as above.

## Where the data comes from

- **Arts and quartz** for Sky FC, Sky SC, Sky the 3rd, and Trails from Zero are derived from the **Kiseki / Trails** Fandom wiki tables—for example [List of orbal arts (Sky FC)](https://kiseki.fandom.com/wiki/List_of_orbal_arts_(Sky_FC)) and [List of quartz (Sky FC)](https://kiseki.fandom.com/wiki/List_of_quartz_(Sky_FC)). Wiki text may be under **CC-BY-SA**; see [Fandom licensing](https://www.fandom.com/licensing) if you copy effect or description prose verbatim.
- **`characters.json`:** Orbment slot layouts are hand-maintained JSON and are not produced by the wiki build script.

## License

Licensed under the **MIT License** — see [LICENSE](LICENSE).
