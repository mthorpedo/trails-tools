import importlib.util
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_trails_game_data.py"
SPEC = importlib.util.spec_from_file_location("validate_trails_game_data", SCRIPT)
validator_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator_module)


class ValidateTrailsGameDataTests(unittest.TestCase):
    def run_validator(self, root, *args):
        with patch.object(validator_module.Path, "resolve", return_value=(root / "scripts" / "validate_trails_game_data.py").resolve()):
            with patch("sys.argv", ["validate_trails_game_data.py", *args]), redirect_stdout(StringIO()):
                try:
                    validator_module.main()
                except SystemExit as exc:
                    return exc.code
        return 0

    def make_fixture(self):
        temp_dir = tempfile.TemporaryDirectory()
        fixture_root = Path(temp_dir.name)
        shutil.copytree(ROOT / "games", fixture_root / "games")
        shutil.copy2(ROOT / "orbment-planner.html", fixture_root / "orbment-planner.html")
        (fixture_root / "scripts").mkdir()
        return temp_dir, fixture_root

    def test_repository_data_is_valid(self):
        self.assertEqual(self.run_validator(ROOT), 0)

    def test_empty_arrays_are_valid(self):
        temp_dir, root = self.make_fixture()
        self.addCleanup(temp_dir.cleanup)
        game = root / "games" / "sky-fc"
        for filename in ("characters.json", "quartz.json", "arts.json"):
            (game / filename).write_text("[]\n", encoding="utf-8")
        self.assertEqual(self.run_validator(root, "--game", "sky-fc"), 0)

    def test_non_dense_quartz_types_fail(self):
        temp_dir, root = self.make_fixture()
        self.addCleanup(temp_dir.cleanup)
        path = root / "games" / "sky-fc" / "quartz.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data[0]["type"] = 99
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.run_validator(root, "--game", "sky-fc"), 1)

    def test_malformed_json_fails(self):
        temp_dir, root = self.make_fixture()
        self.addCleanup(temp_dir.cleanup)
        path = root / "games" / "sky-fc" / "arts.json"
        path.write_text("not json\n", encoding="utf-8")
        self.assertEqual(self.run_validator(root, "--game", "sky-fc"), 1)

    def test_unregistered_game_fails(self):
        temp_dir, root = self.make_fixture()
        self.addCleanup(temp_dir.cleanup)
        shutil.copytree(root / "games" / "sky-fc", root / "games" / "new-game")
        self.assertEqual(self.run_validator(root), 1)


if __name__ == "__main__":
    unittest.main()
