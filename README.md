# Trails orbment planner

[![GitHub stars](https://img.shields.io/github/stars/OWNER/REPO?style=flat-square&logo=github)](https://github.com/OWNER/REPO/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

Replace `OWNER` and `REPO` in the stars badge URL with your GitHub username and repository name after you publish the repo.

Static **HTML**, **JavaScript**, and **CSS** orbment planner for several *Trails* / *Kiseki* titles. Per-game data lives under [`games/sky-fc`](games/sky-fc), [`games/sky-sc`](games/sky-sc), [`games/sky-tc`](games/sky-tc), and [`games/zero`](games/zero) as `characters.json`, `quartz.json`, and `arts.json`. Full schemas, UI rules, and wiki pipeline details are in [`COMPREHENSIVE-PLAN.md`](COMPREHENSIVE-PLAN.md).

## Tools and how to use them

### Orbment planner (hosted)

Choose a **game** and **character**. You can assign quartz to slots, inspect **line sepith totals**, and see **enabled arts** for the current loadout. Behavior matches [COMPREHENSIVE-PLAN.md §5](COMPREHENSIVE-PLAN.md).

### Wiki data build / maintenance

[`scripts/build_trails_wiki_data.py`](scripts/build_trails_wiki_data.py) refreshes **`arts.json`** and **`quartz.json`** from cached Fandom wiki HTML (not needed to simply use the hosted planner).

- **Regenerate** for a title: `curl` MediaWiki `action=parse` JSON into the paths listed in `GAME_INPUTS` inside the script (see the script docstring and [COMPREHENSIVE-PLAN.md §6.6](COMPREHENSIVE-PLAN.md)), then run for example:
  - `python3 scripts/build_trails_wiki_data.py sky-fc` | `sky-sc` | `sky-tc` | `zero`
- **`--resort-json-only`** — Re-sort `arts.json`, `quartz.json`, and `characters.json` under each `games/*/` without fetching the wiki.
- **`--reassign-quartz-types-only`** — Recompute quartz **`type`** ids from the script’s rules for every `games/*/quartz.json`.

**Dependencies:** Python 3 and **BeautifulSoup** (the script prepends [`.build_deps/`](.build_deps/) to `sys.path`). For exact `curl` commands and column mapping, use **§6** of the comprehensive plan.

## Contributing

For development and local checks (not required for GitHub Pages visitors):

- **Local preview:** Browsers block `fetch()` on `file://`. Clone the repo, run a static HTTP server at the **project root** (for example `python3 -m http.server`), and open `http://localhost:PORT/` so relative `games/...` URLs resolve. See [COMPREHENSIVE-PLAN.md §1](COMPREHENSIVE-PLAN.md) **Serving** for background.
- **Workflow:** Branch from `main`. After changing wiki import logic or Fandom pages, refresh `/tmp` caches with `curl`, then run `build_trails_wiki_data.py` for the affected game id. Use `--reassign-quartz-types-only` or `--resort-json-only` only when you intend those rewrites. Keep JSON and UI changes consistent with [COMPREHENSIVE-PLAN.md](COMPREHENSIVE-PLAN.md).

Pull requests are welcome once the repository is public; use GitHub **Issues** for the same `OWNER/REPO` as above.

## Where the data comes from

- **Arts and quartz** for Sky FC, Sky SC, Sky the 3rd, and Trails from Zero are derived from the **Kiseki / Trails** Fandom wiki tables—for example [List of orbal arts (Sky FC)](https://kiseki.fandom.com/wiki/List_of_orbal_arts_(Sky_FC)) and [List of quartz (Sky FC)](https://kiseki.fandom.com/wiki/List_of_quartz_(Sky_FC)), with matching list pages for the other titles (see [COMPREHENSIVE-PLAN.md §6.1](COMPREHENSIVE-PLAN.md)). Wiki text may be under **CC-BY-SA**; see [Fandom licensing](https://www.fandom.com/licensing) if you copy effect or description prose verbatim.
- **`characters.json`:** The Sky FC party layout is seeded in-repo. **`sky-sc`**, **`sky-tc`**, and **`zero`** orbment slot layouts are **hand-maintained** JSON and are **not** produced by the wiki build script (see [COMPREHENSIVE-PLAN.md §4](COMPREHENSIVE-PLAN.md) and §8).

## License

Licensed under the **MIT License** — see [LICENSE](LICENSE).
