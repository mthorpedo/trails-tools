import importlib.util
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_trails_wiki_data.py"
SPEC = importlib.util.spec_from_file_location("build_trails_wiki_data", SCRIPT)
builder_module = importlib.util.module_from_spec(SPEC)
try:
    SPEC.loader.exec_module(builder_module)
except ModuleNotFoundError as exc:
    if exc.name != "bs4":
        raise
    raise unittest.SkipTest("build_trails_wiki_data.py requires BeautifulSoup; install it in .build_deps to run importer tests")


ARTS_HTML = """
<table class="article-table">
  <tr><th>header</th></tr>
  <tr>
    <td rowspan="2"><img alt="Fire orbment" /></td>
    <td rowspan="2"><b>Fire Bolt</b></td>
    <td><span style="white-space: nowrap"><img alt="Fire" />× 3<img alt="Wind" />× 2</span></td>
    <td>10 EP</td><td>Cast: 20 AT\nDelay: 30 AT</td><td>40</td><td>Single</td>
  </tr>
  <tr><td>Deals fire damage.</td><td>Area</td></tr>
</table>
"""


QUARTZ_HTML = """
<table class="article-table">
  <tr><th>Icon</th><th>Name</th><th>Effect</th><th>Elemental Value</th><th>Synthesis Cost</th><th>Location</th></tr>
  <tr>
    <td><img alt="Earth" /></td><td><b>Defense 1</b></td><td>DEF +5%</td>
    <td><span style="white-space: nowrap"><img alt="Earth" />× 1</span></td><td>50</td><td>Shop</td>
  </tr>
</table>
<table class="article-table">
  <tr><th>Icon</th><th>Slot Upgrade</th><th>Name</th><th>Effect</th><th>Elemental Value</th><th>Synthesis Cost</th><th>Location</th></tr>
  <tr>
    <td><img alt="Wind" /></td><td>None</td><td><b>Evade 1</b></td><td>EVA +5%</td>
    <td><span style="white-space: nowrap"><img alt="Wind" />× 2</span></td><td>80</td><td>Shop</td>
  </tr>
</table>
"""


class BuildTrailsWikiDataTests(unittest.TestCase):
    def test_parse_arts_html_reads_two_row_art_and_elemental_costs(self):
        arts = builder_module.parse_arts_html(ARTS_HTML)

        self.assertEqual(len(arts), 1)
        self.assertEqual(
            arts[0],
            {
                "name": "Fire Bolt",
                "description": "Deals fire damage.",
                "elemental": "fire",
                "elemental-value": {
                    "earth": 0,
                    "water": 0,
                    "fire": 3,
                    "wind": 2,
                    "time": 0,
                    "space": 0,
                    "mirage": 0,
                },
                "cost": 10,
                "time": {"cast": 20, "delay": 30},
                "power": 40,
                "target-effect": "Single\nArea",
            },
        )

    def test_parse_quartz_html_supports_fc_and_sc_table_layouts(self):
        quartz = builder_module.parse_quartz_html(QUARTZ_HTML)

        self.assertEqual([q["name"] for q in quartz], ["Defense 1", "Evade 1"])
        self.assertEqual([q["elemental"] for q in quartz], ["earth", "wind"])
        self.assertEqual(quartz[0]["cost"]["earth"], 1)
        self.assertEqual(quartz[1]["cost"]["wind"], 2)

    def test_post_process_quartz_types_applies_all_alias_rules_and_compacts(self):
        names = [
            "Poison", "Mute", "Deathblow 1", "Deathblow 2", "Burn", "Burn 2",
            "Effort", "Prankster", "Defense 1", "Topaz Gem", "Attack 1", "Carnage",
        ]
        quartz = [{"name": name, "type": 0} for name in names]

        builder_module.post_process_quartz_types(quartz)
        types = {q["name"]: q["type"] for q in quartz}

        self.assertEqual(types["Poison"], types["Mute"])
        self.assertEqual(types["Poison"], types["Deathblow 1"])
        self.assertEqual(types["Poison"], types["Deathblow 2"])
        self.assertEqual(types["Poison"], types["Burn"])
        self.assertEqual(types["Poison"], types["Burn 2"])
        self.assertEqual(types["Effort"], types["Prankster"])
        self.assertEqual(types["Defense 1"], types["Topaz Gem"])
        self.assertEqual(types["Attack 1"], types["Carnage"])
        self.assertEqual(set(types.values()), set(range(1, max(types.values()) + 1)))

    def test_output_sorting_uses_canonical_element_and_secondary_keys(self):
        arts = [
            {"elemental": "fire", "target-effect": "B", "cost": 1},
            {"elemental": "earth", "target-effect": "Z", "cost": 99},
            {"elemental": "fire", "target-effect": "A", "cost": 2},
        ]
        quartz = [
            {"elemental": "wind", "type": 2},
            {"elemental": "earth", "type": 3},
            {"elemental": "earth", "type": 1},
        ]

        self.assertEqual(
            [art["target-effect"] for art in builder_module.sort_arts_for_output(arts)],
            ["Z", "A", "B"],
        )
        self.assertEqual(
            [(q["elemental"], q["type"]) for q in builder_module.sort_quartz_for_output(quartz)],
            [("earth", 1), ("earth", 3), ("wind", 2)],
        )

    def test_main_import_writes_parsed_and_sorted_json_to_selected_game(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "scripts").mkdir()
            output_dir = root / "games" / "sky-fc"
            output_dir.mkdir(parents=True)
            arts_cache = root / "arts.json"
            quartz_cache = root / "quartz.json"
            arts_cache.write_text(json.dumps({"parse": {"text": {"*": ARTS_HTML}}}), encoding="utf-8")
            quartz_cache.write_text(json.dumps({"parse": {"text": {"*": QUARTZ_HTML}}}), encoding="utf-8")

            with patch.dict(builder_module.GAME_INPUTS, {"sky-fc": (arts_cache, quartz_cache)}):
                with patch.object(builder_module.Path, "resolve", return_value=root / "scripts" / "build_trails_wiki_data.py"):
                    with patch.object(sys, "argv", ["build_trails_wiki_data.py", "sky-fc"]), redirect_stdout(StringIO()):
                        builder_module.main()

            arts = json.loads((output_dir / "arts.json").read_text(encoding="utf-8"))
            quartz = json.loads((output_dir / "quartz.json").read_text(encoding="utf-8"))
            self.assertEqual([art["name"] for art in arts], ["Fire Bolt"])
            self.assertEqual([q["name"] for q in quartz], ["Defense 1", "Evade 1"])
            self.assertTrue(all(q["type"] > 0 for q in quartz))


if __name__ == "__main__":
    unittest.main()
