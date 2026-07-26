#!/usr/bin/env python3
"""Validate Trails game data and game-selector registration without rewriting files."""
import argparse
import json
import re
from pathlib import Path


ELEMENTS = ("earth", "water", "fire", "wind", "time", "space", "mirage")
REQUIRED_GAME_FILES = ("characters.json", "quartz.json", "arts.json")


class Validator:
    def __init__(self):
        self.errors = []

    def error(self, path, message):
        self.errors.append(f"{path}: {message}")

    def require(self, value, path, message):
        if not value:
            self.error(path, message)
        return value


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def validate_element_map(value, path, validator):
    if not isinstance(value, dict):
        validator.error(path, "must be an object with exactly the seven element keys")
        return
    keys = set(value)
    if keys != set(ELEMENTS):
        validator.error(path, f"must have exactly these keys: {', '.join(ELEMENTS)}")
    for element in ELEMENTS:
        number = value.get(element)
        if not is_int(number) or number < 0:
            validator.error(f"{path}.{element}", "must be a non-negative integer")


def validate_names(items, path, validator, require_unique=True):
    names = []
    for index, item in enumerate(items):
        item_path = f"{path}[{index}]"
        if not isinstance(item, dict):
            validator.error(item_path, "must be an object")
            continue
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            validator.error(f"{item_path}.name", "must be a non-empty string")
            continue
        names.append(name)
    if require_unique and len(names) != len(set(names)):
        validator.error(path, "names must be unique")
    return names


def validate_characters(items, path, validator):
    names = validate_names(items, path, validator)
    if names != sorted(names, key=str.casefold):
        validator.error(path, "characters must be ordered alphabetically by name (case-insensitive)")
    for index, character in enumerate(items):
        if not isinstance(character, dict):
            continue
        item_path = f"{path}[{index}]"
        if not isinstance(character.get("guest"), bool):
            validator.error(f"{item_path}.guest", "must be a boolean")
        orbment = character.get("orbment")
        if not isinstance(orbment, list) or not orbment:
            validator.error(f"{item_path}.orbment", "must be a non-empty array")
            continue
        for slot_index, slot in enumerate(orbment):
            slot_path = f"{item_path}.orbment[{slot_index}]"
            if not isinstance(slot, dict):
                validator.error(slot_path, "must be an object")
                continue
            elemental = slot.get("elemental")
            if elemental is not None and elemental not in ELEMENTS:
                validator.error(f"{slot_path}.elemental", "must be null or a canonical element")
            if not is_int(slot.get("line")):
                validator.error(f"{slot_path}.line", "must be an integer")


def validate_quartz(items, path, validator):
    validate_names(items, path, validator, require_unique=False)
    types = []
    for index, quartz in enumerate(items):
        if not isinstance(quartz, dict):
            continue
        item_path = f"{path}[{index}]"
        qtype = quartz.get("type")
        if not is_int(qtype) or qtype <= 0:
            validator.error(f"{item_path}.type", "must be a positive integer")
        else:
            types.append(qtype)
        if quartz.get("elemental") not in ELEMENTS:
            validator.error(f"{item_path}.elemental", "must be a canonical element")
        validate_element_map(quartz.get("cost"), f"{item_path}.cost", validator)
        if not isinstance(quartz.get("effect"), str):
            validator.error(f"{item_path}.effect", "must be a string")
        if not is_int(quartz.get("level")) or quartz["level"] < 0:
            validator.error(f"{item_path}.level", "must be a non-negative integer")
    if types and set(types) != set(range(1, max(types) + 1)):
        validator.error(path, "quartz type ids must be dense from 1 through their maximum")


def validate_arts(items, path, validator):
    validate_names(items, path, validator)
    for index, art in enumerate(items):
        if not isinstance(art, dict):
            continue
        item_path = f"{path}[{index}]"
        for field in ("description", "target-effect"):
            if not isinstance(art.get(field), str):
                validator.error(f"{item_path}.{field}", "must be a string")
        if art.get("elemental") not in ELEMENTS:
            validator.error(f"{item_path}.elemental", "must be a canonical element")
        validate_element_map(art.get("elemental-value"), f"{item_path}.elemental-value", validator)
        for field in ("cost", "power"):
            if not is_int(art.get(field)) or art[field] < 0:
                validator.error(f"{item_path}.{field}", "must be a non-negative integer")
        time = art.get("time")
        if not isinstance(time, dict):
            validator.error(f"{item_path}.time", "must be an object")
        else:
            if set(time) != {"cast", "delay"}:
                validator.error(f"{item_path}.time", "must have exactly cast and delay keys")
            for field in ("cast", "delay"):
                if not is_int(time.get(field)) or time[field] < 0:
                    validator.error(f"{item_path}.time.{field}", "must be a non-negative integer")


def load_array(path, validator):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        validator.error(path, f"cannot parse JSON: {exc}")
        return None
    if not isinstance(value, list):
        validator.error(path, "must contain a JSON array")
        return None
    return value


def selector_game_ids(root, validator):
    page = root / "orbment-planner.html"
    try:
        text = page.read_text(encoding="utf-8")
    except OSError as exc:
        validator.error(page, f"cannot read game selector: {exc}")
        return []
    match = re.search(r'<select[^>]+id=["\']game["\'][^>]*>(.*?)</select>', text, re.S | re.I)
    if not match:
        validator.error(page, "cannot find #game selector")
        return []
    return re.findall(r'<option\s+[^>]*value=["\']([^"\']+)["\']', match.group(1), re.I)


def validate_game(root, game_id, validator):
    game_path = root / "games" / game_id
    for filename in REQUIRED_GAME_FILES:
        path = game_path / filename
        if not path.is_file():
            validator.error(game_path, f"missing required file {filename}")
    characters = load_array(game_path / "characters.json", validator) if (game_path / "characters.json").is_file() else None
    quartz = load_array(game_path / "quartz.json", validator) if (game_path / "quartz.json").is_file() else None
    arts = load_array(game_path / "arts.json", validator) if (game_path / "arts.json").is_file() else None
    if characters is not None:
        validate_characters(characters, str(game_path / "characters.json"), validator)
    if quartz is not None:
        validate_quartz(quartz, str(game_path / "quartz.json"), validator)
    if arts is not None:
        validate_arts(arts, str(game_path / "arts.json"), validator)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", help="Validate one game id instead of every directory under games/")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    validator = Validator()
    games_root = root / "games"
    discovered = sorted(path.name for path in games_root.iterdir() if path.is_dir()) if games_root.exists() else []
    selected = [args.game] if args.game else discovered
    if not selected:
        validator.error(games_root, "contains no game directories")
    selector_ids = selector_game_ids(root, validator)
    for game_id in selected:
        if game_id not in discovered:
            validator.error(games_root, f"game directory {game_id!r} does not exist")
            continue
        validate_game(root, game_id, validator)
        if selector_ids.count(game_id) != 1:
            validator.error("orbment-planner.html #game", f"must register {game_id!r} exactly once")
    if not args.game:
        for game_id in selector_ids:
            if game_id not in discovered:
                validator.error("orbment-planner.html #game", f"registers missing game directory {game_id!r}")
    if validator.errors:
        print("Validation failed:")
        print("\n".join(f"- {error}" for error in validator.errors))
        raise SystemExit(1)
    print(f"Validated {len(selected)} game(s): {', '.join(selected)}")


if __name__ == "__main__":
    main()
