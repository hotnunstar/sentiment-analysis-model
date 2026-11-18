"""Topic 4 tests: integration, contract, scenarios and session logs.

These tests use a small fake engine, so they do not need the large machine
learning model files. Run with:

    python -m unittest tests.test_topic4 -v
"""

import ast
import os
import sys
import tempfile
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from harness.contract import ACTIONS, normalize  # noqa: E402
from harness.scenarios import list_scenarios, load_scenario  # noqa: E402
from harness.session import Session  # noqa: E402


class FakeEngine:
    """Small predictable engine used to test the shared interface."""

    def __init__(self):
        self.reset_count = 0

    def reset(self):
        self.reset_count += 1

    def process(self, text, audio_path=None, image_path=None):
        return {
            "valence": 0.1,
            "activity": 0.2,
            "dominance": 0.0,
            "confidence": 0.8,
            "label": "neutral",
            "action": "ANSWER",
            "reply": "Test reply",
            "flags": [],
            "details": {"received_text": text},
        }


class BrokenEngine(FakeEngine):
    """Engine that fails so the session error handling can be tested."""

    def process(self, text, audio_path=None, image_path=None):
        raise RuntimeError("test failure")


class ContractTests(unittest.TestCase):
    def test_valid_result_has_no_problems(self):
        result = normalize(FakeEngine().process("Hello"))
        self.assertEqual(result["problems"], [])
        self.assertIn(result["action"], ACTIONS)

    def test_invalid_result_is_reported(self):
        result = normalize({"action": "UNKNOWN"})
        self.assertGreater(len(result["problems"]), 0)
        self.assertEqual(result["action"], "ANSWER")


class SessionTests(unittest.TestCase):
    def test_session_sends_message_and_writes_log(self):
        with tempfile.TemporaryDirectory() as log_dir:
            session = Session(FakeEngine(), log_dir=log_dir)
            entry = session.send("Hello", source="test")
            log_path = session.logger.path
            session.close()

            self.assertEqual(entry["id"], 1)
            self.assertEqual(entry["source"], "test")
            self.assertEqual(entry["problems"], [])
            self.assertTrue(os.path.isfile(log_path))

            with open(log_path, encoding="utf-8") as log_file:
                log_text = log_file.read()
            self.assertIn("INPUT      : Hello", log_text)
            self.assertIn("ACTION     : ANSWER", log_text)

    def test_session_survives_engine_error(self):
        session = Session(BrokenEngine(), log=False)
        entry = session.send("Hello")

        self.assertIsNotNone(entry["error"])
        self.assertGreater(len(entry["problems"]), 0)
        self.assertEqual(len(session.history), 1)


class ScenarioTests(unittest.TestCase):
    def test_all_eight_scenarios_exist(self):
        scenarios = list_scenarios(os.path.join(ROOT, "scenarios"))
        self.assertEqual(len(scenarios), 8)

    def test_mandatory_scenarios_have_messages(self):
        mandatory_dir = os.path.join(ROOT, "scenarios", "mandatory")
        names = sorted(name for name in os.listdir(mandatory_dir) if name.endswith(".json"))
        self.assertEqual(len(names), 4)

        ids = []
        for name in names:
            scenario = load_scenario(os.path.join(mandatory_dir, name))
            ids.append(scenario["id"])
            self.assertTrue(scenario["messages"])
            self.assertTrue(all(message.get("text") for message in scenario["messages"]))
        self.assertEqual(ids, ["M1", "M2", "M3", "M4"])


class ProjectFilesTests(unittest.TestCase):
    def test_engine_exposes_the_required_methods(self):
        engine_path = os.path.join(ROOT, "engine", "engine.py")
        with open(engine_path, encoding="utf-8") as engine_file:
            tree = ast.parse(engine_file.read())

        engine_class = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Engine")
        methods = {node.name: node for node in engine_class.body if isinstance(node, ast.FunctionDef)}

        self.assertIn("reset", methods)
        self.assertIn("process", methods)
        process_args = [argument.arg for argument in methods["process"].args.args]
        self.assertEqual(process_args, ["self", "text", "audio_path", "image_path"])

    def test_readme_contains_the_main_commands(self):
        readme_path = os.path.join(ROOT, "README.md")
        with open(readme_path, encoding="utf-8") as readme_file:
            readme = readme_file.read()

        required_commands = (
            "python check_project.py",
            "python run_app.py",
            "python run_scenario.py",
            "python -m unittest discover tests",
        )
        for command in required_commands:
            self.assertIn(command, readme)


if __name__ == "__main__":
    unittest.main(verbosity=2)
