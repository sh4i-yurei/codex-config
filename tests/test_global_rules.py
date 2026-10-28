"""Check the instructions loaded as Codex's global rules."""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "global-rules.md"


class GlobalRulesTests(unittest.TestCase):
    def test_roles_section_points_to_operating_model(self):
        text = RULES.read_text()
        match = re.search(
            r"^## 1\. Roles and workflow\n(?P<body>.*?)(?=^## |\Z)",
            text,
            re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(match)
        body = match.group("body")
        with self.subTest(case="path"):
            self.assertIn(
                "~/Documents/Second_Brain/10_Projects/Operating model.md", body
            )
        for phrase in (
            "starting new work",
            "where a decision belongs",
            "two notes disagree",
            "new kind of work",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, body)

    def test_operating_model_is_named_once(self):
        text = RULES.read_text()
        self.assertEqual(text.count("Operating model.md"), 1)

    def test_operating_model_decisions_are_not_copied(self):
        text = RULES.read_text()
        for title in (
            "Workflows are global",
            "An agent owns what it creates",
            "Build effort is never a reason for a design",
        ):
            with self.subTest(title=title):
                self.assertNotIn(title, text)

    def test_building_from_a_handoff_covers_the_required_contract(self):
        text = RULES.read_text()
        match = re.search(
            r"^## Building from a handoff\n(?P<body>.*?)(?=^## |\Z)",
            text,
            re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(match)
        body = match.group("body").strip()
        self.assertLessEqual(len(body.splitlines()), 25)
        for expected in (
            "repository's `AGENTS.md` and `ARCHITECTURE.md`",
            "what each piece must not do",
            "Open questions and stop",
            "dependency, tool or pattern the handoff doesn't name",
            "shared interface",
            "test case",
            "API, flag, configuration key and import",
            "lookup.py",
            "tests from the handoff's cases first",
            "failing on an assertion",
            "existing behaviour",
            "killing mutants",
            "decision 11",
            "Never weaken a test",
            "behaviour, not implementation",
            "complete",
            "current code and tests",
            "cache invalidation",
            "timestamps",
            "no test of behaviour can kill it",
            "only a test pinning an internal detail could kill",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, body)

    def test_git_section_limits_build_handoff_pushes(self):
        text = RULES.read_text()
        match = re.search(
            r"^## 6\. Git\n(?P<body>.*?)(?=^## |\Z)",
            text,
            re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(match)
        handoff_paragraph = next(
            paragraph
            for paragraph in match.group("body").strip().split("\n\n")
            if paragraph.startswith("A build handoff")
        )
        self.assertEqual(
            " ".join(handoff_paragraph.split()),
            "A build handoff authorizes pushing its named branch only. "
            "Always push with the branch named; never push main, force-push, "
            "open or edit a pull request, or merge under that handoff.",
        )


if __name__ == "__main__":
    unittest.main()
