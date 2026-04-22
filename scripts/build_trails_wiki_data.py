#!/usr/bin/env python3
"""Parse wiki HTML (MediaWiki JSON) -> games/{sky-fc|sky-sc|sky-tc|zero}/arts.json and quartz.json.

Wiki import requires a game id (no default). Sky trilogy: sky-fc (Sky FC), sky-sc (Sky SC), sky-tc (Sky the 3rd); Crossbell: zero.

Prerequisite: curl MediaWiki parse JSON to /tmp (see GAME_INPUTS) then run:
  python3 scripts/build_trails_wiki_data.py sky-fc
  python3 scripts/build_trails_wiki_data.py sky-sc
  python3 scripts/build_trails_wiki_data.py sky-tc
  python3 scripts/build_trails_wiki_data.py zero

Re-sort existing games/*/ JSON without wiki (characters alphabetical; arts/quartz orders per COMPREHENSIVE-PLAN §6.3):
  python3 scripts/build_trails_wiki_data.py --resort-json-only

Recompute quartz `type` fields from names only (no wiki; same rules as a fresh import):
  python3 scripts/build_trails_wiki_data.py --reassign-quartz-types-only
"""
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".build_deps"))
from bs4 import BeautifulSoup

ELEMENTS = ("earth", "water", "fire", "wind", "time", "space", "mirage")


def zero_cost():
    return {k: 0 for k in ELEMENTS}


def alt_to_element(alt: str) -> Optional[str]:
    if not alt:
        return None
    first = alt.strip().split()[0].lower()
    if first in ELEMENTS:
        return first
    return None


def parse_elemental_value_cell(td) -> dict:
    """Sum sepith costs from each nowrap chunk: icon(s) + × digits in wiki order."""
    out = zero_cost()
    for wrap in td.find_all("span", attrs={"style": re.compile("nowrap", re.I)}):
        imgs = wrap.find_all("img")
        nums = re.findall(r"\d+", wrap.get_text())
        if not imgs or not nums:
            continue
        n_use = min(len(imgs), len(nums))
        for i in range(n_use):
            key = alt_to_element(imgs[i].get("alt") or "")
            if key:
                out[key] += int(nums[i])
    if sum(out.values()) == 0:
        # Fallback: any img in cell with trailing digits in cell text
        imgs = td.find_all("img")
        nums = re.findall(r"\d+", td.get_text())
        for i in range(min(len(imgs), len(nums))):
            key = alt_to_element(imgs[i].get("alt") or "")
            if key:
                out[key] += int(nums[i])
    return out


def first_icon_elemental(td) -> str:
    """First column icon alt -> elemental string (wiki section element)."""
    img = td.find("img")
    if img:
        k = alt_to_element(img.get("alt") or "")
        if k:
            return k
    return "earth"


def parse_time_cell(text: str) -> dict:
    cast = delay = 0
    m1 = re.search(r"Cast:\s*(\d+)\s*AT", text, re.I)
    m2 = re.search(r"Delay:\s*(\d+)\s*AT", text, re.I)
    if m1:
        cast = int(m1.group(1))
    if m2:
        delay = int(m2.group(1))
    return {"cast": cast, "delay": delay}


def parse_cost_ep(text: str) -> int:
    m = re.search(r"(\d+)\s*EP", text, re.I)
    return int(m.group(1)) if m else 0


def parse_power(text: str) -> int:
    t = text.strip()
    if not t or t in ("—", "-", "—"):
        return 0
    m = re.search(r"-?\d+", t)
    return int(m.group(0)) if m else 0


def parse_arts_html(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    arts = []
    for table in soup.find_all("table", class_="article-table"):
        rows = table.find_all("tr")
        i = 1
        while i < len(rows):
            tr = rows[i]
            tds = tr.find_all("td", recursive=False)
            if len(tds) < 7:
                i += 1
                continue
            td0, td1, td2, td3, td4, td5, td6 = tds[:7]
            if td0.get("rowspan") != "2" or td1.get("rowspan") != "2":
                i += 1
                continue
            name = td1.find("b")
            name_txt = name.get_text(strip=True) if name else td1.get_text(" ", strip=True)
            name_txt = re.sub(r"\s+", " ", name_txt).split()[0] if name_txt else ""
            # English only: first word before Japanese often glued - take before first non-ascii block
            raw_name = td1.get_text("\n", strip=True)
            lines_nm = [x.strip() for x in raw_name.split("\n") if x.strip()]
            if lines_nm:
                name_txt = lines_nm[0]

            elemental = first_icon_elemental(td0)
            ev = parse_elemental_value_cell(td2)
            cost = parse_cost_ep(td3.get_text(" ", strip=True))
            time_obj = parse_time_cell(td4.get_text("\n", strip=True))
            power = parse_power(td5.get_text(strip=True))
            target = td6.get_text("\n", strip=True)

            desc_parts = []
            if i + 1 < len(rows):
                tr2 = rows[i + 1]
                tds2 = tr2.find_all("td", recursive=False)
                if len(tds2) == 2:
                    desc_parts.append(tds2[0].get_text("\n", strip=True))
                    t2 = tds2[1].get_text("\n", strip=True)
                    if t2 and t2 != "—":
                        target = (target + "\n" + t2).strip()
                    i += 2
                else:
                    i += 1
            else:
                i += 1

            description = "\n".join(desc_parts) if desc_parts else ""

            arts.append(
                {
                    "name": name_txt,
                    "description": description,
                    "elemental": elemental,
                    "elemental-value": ev,
                    "cost": cost,
                    "time": time_obj,
                    "power": power,
                    "target-effect": target,
                }
            )
    return arts


def _parse_quartz_row_fc(tds) -> Optional[dict]:
    """FC layout: 6 columns — icon, name, effect, elemental value, …"""
    if len(tds) < 6:
        return None
    td0, td1, td2, td3 = tds[0], tds[1], tds[2], tds[3]
    if not td0.find("img"):
        return None
    elemental = first_icon_elemental(td0)
    b = td1.find("b")
    name_txt = b.get_text(strip=True) if b else td1.get_text(" ", strip=True)
    name_txt = re.sub(r"\s+", " ", name_txt)
    effect = td2.get_text("\n", strip=True)
    cost = parse_elemental_value_cell(td3)
    return {
        "name": name_txt,
        "type": 0,
        "elemental": elemental,
        "cost": cost,
        "effect": effect,
        "level": 1,
    }


def _parse_quartz_row_sc(tds) -> Optional[dict]:
    """SC layout: 7 columns — quartz icon, slot upgrade (ignored), name, effect, elemental value, synthesis, location."""
    if len(tds) < 7:
        return None
    td0, _td_slot_upgrade, td2, td3, td4 = tds[0], tds[1], tds[2], tds[3], tds[4]
    if not td0.find("img"):
        return None
    elemental = first_icon_elemental(td0)
    b = td2.find("b")
    name_txt = b.get_text(strip=True) if b else td2.get_text(" ", strip=True)
    name_txt = re.sub(r"\s+", " ", name_txt)
    effect = td3.get_text("\n", strip=True)
    cost = parse_elemental_value_cell(td4)
    return {
        "name": name_txt,
        "type": 0,
        "elemental": elemental,
        "cost": cost,
        "effect": effect,
        "level": 1,
    }


def parse_quartz_html(html: str) -> list:
    """Parse quartz wikitables. FC uses 6-column rows; Sky SC uses 7 (Location + slot upgrade col)."""
    soup = BeautifulSoup(html, "html.parser")
    quartz = []
    for table in soup.find_all("table", class_="article-table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        header_cells = rows[0].find_all(["th", "td"])
        heads = [c.get_text(strip=True).lower() for c in header_cells]
        joined = " ".join(heads)
        if "elemental value" not in joined or "synthesis cost" not in joined:
            continue
        # Sky SC adds a slot-upgrade column: 7 headers / 7 body cells. FC has Location but only 6 columns.
        use_sc_layout = len(header_cells) >= 7
        for tr in rows[1:]:
            tds = tr.find_all("td", recursive=False)
            if use_sc_layout:
                row = _parse_quartz_row_sc(tds)
            else:
                row = _parse_quartz_row_fc(tds)
            if row:
                quartz.append(row)
    return quartz


def assign_quartz_types_by_name_group(quartz_list):
    """Set type from 1..N: same base name + trailing digit (e.g. Defense 1/2/3) share one type."""

    def group_key(name):
        m = re.match(r"^(.*)\s+(\d+)\s*$", name.strip())
        if m:
            return m.group(1).strip()
        return name.strip()

    order = []
    for q in quartz_list:
        k = group_key(q["name"])
        if k not in order:
            order.append(k)
    key_to_type = {k: i + 1 for i, k in enumerate(order)}
    for q in quartz_list:
        q["type"] = key_to_type[group_key(q["name"])]


# Quartz that share Poison's type id (orbment exclusivity): status/debuff set plus Strike / Death / Deathblow tiers,
# and Burn (Crossbell / Zero-style burn proc quartz).
STATUS_QUARTZ_NAMES = frozenset(
    {
        "Poison",
        "Mute",
        "Petrify",
        "Freeze",
        "Seal",
        "Confuse",
        "Sleep",
        "Blind",
        "Strike",
        "Death",
        "Deathblow 1",
        "Deathblow 2",
        "Nothingness",
        "Burn",
        "Burn 2",
    }
)


def assign_status_quartz_shared_type(quartz_list):
    poison = next((q for q in quartz_list if q.get("name") == "Poison"), None)
    if not poison:
        return
    shared = poison["type"]
    for q in quartz_list:
        if q.get("name") in STATUS_QUARTZ_NAMES:
            q["type"] = shared


# Effort / Prankster: cooking-related quartz share one exclusivity type (Trails from Zero).
EFFORT_PRANKSTER_QUARTZ_NAMES = frozenset({"Effort", "Prankster"})


def assign_effort_prankster_shared_type(quartz_list):
    effort = next((q for q in quartz_list if q.get("name") == "Effort"), None)
    prankster = next((q for q in quartz_list if q.get("name") == "Prankster"), None)
    src = effort or prankster
    if not src:
        return
    shared = src["type"]
    for q in quartz_list:
        if q.get("name") in EFFORT_PRANKSTER_QUARTZ_NAMES:
            q["type"] = shared


# Gem quartz: same exclusivity `type` as the tiered line they replace (wiki uses gem name; no "Defense 5" row).
# Source names are any row in that line's group (tier 1 shares type with all tiers in the group).
GEM_TYPE_SOURCE_NAME = {
    "Topaz Gem": "Defense 1",
    "Water Gem": "HP 1",
    "Sapphire Gem": "Mind 1",
    "Ruby Gem": "Attack 1",
    "Emerald Gem": "Shield 1",
    "Wind Gem": "Evade 1",
    "Wood Gem": "Impede 1",
    "Onyx Gem": "Action 1",
    "Time Gem": "Cast 1",
    "Gold Gem": "EP Cut 1",
    "Silver Gem": "EP 1",
    "Mirage Gem": "Hit 1",
}

# Carnage (Sky the 3rd): same exclusivity `type` as the Attack tier line; wiki may omit Attack 5/6 rows.
CARNAGE_ATTACK_SOURCES = (
    "Attack 6",
    "Attack 5",
    "Attack 4",
    "Attack 3",
    "Attack 2",
    "Attack 1",
)


def assign_carnage_attack_alias(quartz_list):
    """Assign Carnage the same `type` as Attack 6 if present, else highest Attack N in the list."""
    name_to_type = {q["name"]: q["type"] for q in quartz_list if q.get("name")}
    src = None
    for source_name in CARNAGE_ATTACK_SOURCES:
        src = name_to_type.get(source_name)
        if src is not None:
            break
    if src is None:
        return
    for q in quartz_list:
        if q.get("name") == "Carnage":
            q["type"] = src
            break


def assign_gem_type_aliases(quartz_list):
    """Assign gem quartz the same `type` as their logical tier-N line (see GEM_TYPE_SOURCE_NAME)."""
    name_to_type = {q["name"]: q["type"] for q in quartz_list if q.get("name")}
    for gem_name, source_name in GEM_TYPE_SOURCE_NAME.items():
        src = name_to_type.get(source_name)
        if src is None:
            continue
        for q in quartz_list:
            if q.get("name") == gem_name:
                q["type"] = src
                break


def compact_quartz_types(quartz_list):
    """Remap type integers to 1..N with no gaps, preserving equality of types."""
    uniq = sorted({q["type"] for q in quartz_list})
    old_to_new = {old: i + 1 for i, old in enumerate(uniq)}
    for q in quartz_list:
        q["type"] = old_to_new[q["type"]]


def post_process_quartz_types(quartz_list):
    """Assign logical `type` ids for exclusivity rules (same order as wiki import)."""
    assign_quartz_types_by_name_group(quartz_list)
    assign_status_quartz_shared_type(quartz_list)
    assign_effort_prankster_shared_type(quartz_list)
    assign_gem_type_aliases(quartz_list)
    assign_carnage_attack_alias(quartz_list)
    compact_quartz_types(quartz_list)


def elemental_sort_key(elemental: Optional[str]) -> tuple:
    """Sort key: canonical ELEMENTS order, then unknown element strings."""
    if elemental is None or str(elemental).strip() == "":
        return (len(ELEMENTS), "")
    e = str(elemental).lower().strip()
    try:
        return (ELEMENTS.index(e), e)
    except ValueError:
        return (len(ELEMENTS), e)


def sort_arts_for_output(arts):
    """Arts: elemental (ELEMENTS order), target-effect, EP cost."""

    def art_key(a):
        cost = a.get("cost")
        if isinstance(cost, (int, float)):
            c = int(cost)
        else:
            c = 0
        return (
            elemental_sort_key(a.get("elemental")),
            a.get("target-effect") or "",
            c,
        )

    return sorted(arts, key=art_key)


def sort_quartz_for_output(quartz_list):
    """Quartz: elemental (ELEMENTS order), then type id."""

    def q_key(q):
        t = q.get("type")
        ti = int(t) if isinstance(t, (int, float)) else -1
        return (elemental_sort_key(q.get("elemental")), ti)

    return sorted(quartz_list, key=q_key)


def sort_characters_for_output(characters):
    """Characters: alphabetical by name (case-insensitive)."""
    if not characters:
        return characters
    return sorted(characters, key=lambda c: (c.get("name") or "").casefold())


def resort_existing_game_json(root: Path, game: str) -> None:
    """Rewrite games/{game}/*.json with canonical sort orders (no wiki fetch)."""
    gdir = root / "games" / game
    arts_path = gdir / "arts.json"
    quartz_path = gdir / "quartz.json"
    char_path = gdir / "characters.json"
    if arts_path.exists():
        arts = json.loads(arts_path.read_text(encoding="utf-8"))
        if isinstance(arts, list):
            arts_path.write_text(
                json.dumps(sort_arts_for_output(arts), indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
    if quartz_path.exists():
        qz = json.loads(quartz_path.read_text(encoding="utf-8"))
        if isinstance(qz, list):
            quartz_path.write_text(
                json.dumps(sort_quartz_for_output(qz), indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
    if char_path.exists():
        ch = json.loads(char_path.read_text(encoding="utf-8"))
        if isinstance(ch, list):
            char_path.write_text(
                json.dumps(sort_characters_for_output(ch), indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )


GAME_INPUTS = {
    "sky-fc": (
        Path("/tmp/trails_fc_arts.json"),
        Path("/tmp/trails_fc_quartz.json"),
    ),
    "sky-sc": (
        Path("/tmp/trails_sc_arts.json"),
        Path("/tmp/trails_sc_quartz.json"),
    ),
    "sky-tc": (
        Path("/tmp/trails_tc_arts.json"),
        Path("/tmp/trails_tc_quartz.json"),
    ),
    "zero": (
        Path("/tmp/trails_zero_arts.json"),
        Path("/tmp/trails_zero_quartz.json"),
    ),
}


def main():
    parser = argparse.ArgumentParser(description="Build arts.json and quartz.json from cached wiki parse JSON.")
    parser.add_argument(
        "--resort-json-only",
        action="store_true",
        help="Sort arts, quartz, and characters under games/{sky-fc,sky-sc,sky-tc,zero}/ (no wiki fetch).",
    )
    parser.add_argument(
        "--reassign-quartz-types-only",
        action="store_true",
        help="Recompute quartz type ids from names for all games/*/quartz.json (no wiki fetch).",
    )
    parser.add_argument(
        "game",
        nargs="?",
        choices=sorted(GAME_INPUTS.keys()),
        metavar="GAME",
        help="Game id for wiki import: sky-fc, sky-sc, sky-tc, or zero (required unless using a --*-only flag).",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.resort_json_only or args.reassign_quartz_types_only:
        if args.game is not None:
            parser.error("do not pass GAME with --resort-json-only or --reassign-quartz-types-only")
    else:
        if args.game is None:
            parser.error(
                "GAME is required: sky-fc | sky-sc | sky-tc | zero "
                "(e.g. python3 scripts/build_trails_wiki_data.py sky-fc)"
            )

    if args.resort_json_only:
        for gid in sorted(GAME_INPUTS.keys()):
            resort_existing_game_json(root, gid)
            print("resorted", gid)
        return

    if args.reassign_quartz_types_only:
        for gid in sorted(GAME_INPUTS.keys()):
            qp = root / "games" / gid / "quartz.json"
            if not qp.exists():
                continue
            qz = json.loads(qp.read_text(encoding="utf-8"))
            if not isinstance(qz, list):
                continue
            post_process_quartz_types(qz)
            qz = sort_quartz_for_output(qz)
            qp.write_text(
                json.dumps(qz, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            print("reassigned quartz types", gid, "count", len(qz))
        return

    game = args.game
    arts_path, quartz_path = GAME_INPUTS[game]
    if not arts_path.exists() or not quartz_path.exists():
        print(
            f"Missing cached wiki JSON for {game}:\n  {arts_path}\n  {quartz_path}\nRun curl first (see COMPREHENSIVE-PLAN.md).",
            file=sys.stderr,
        )
        sys.exit(1)
    html_a = json.loads(arts_path.read_text())["parse"]["text"]["*"]
    html_q = json.loads(quartz_path.read_text())["parse"]["text"]["*"]
    arts = parse_arts_html(html_a)
    qz = parse_quartz_html(html_q)
    post_process_quartz_types(qz)
    arts = sort_arts_for_output(arts)
    qz = sort_quartz_for_output(qz)
    out_dir = root / "games" / game
    (out_dir / "arts.json").write_text(
        json.dumps(arts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (out_dir / "quartz.json").write_text(
        json.dumps(qz, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(game, "arts", len(arts), "quartz", len(qz))


if __name__ == "__main__":
    main()
