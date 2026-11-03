"""Check the instructions loaded as Codex's global rules."""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "global-rules.md"
BUILD_SKILL = ROOT / "skills" / "build-from-spec" / "SKILL.md"


class GlobalRulesTests(unittest.TestCase):
    def efficiency_section(self):
        text = RULES.read_text()
        heading = "## 11. Working efficiently"
        marker = "<!-- context7 -->"
        self.assertEqual(text.count(heading), 1)
        self.assertLess(
            text.index("## 10. Designing code and estimating work"), text.index(heading)
        )
        self.assertLess(text.index(heading), text.index(marker))
        return text[text.index(heading) : text.index(marker)].strip()

    def test_efficiency_section_follows_design_and_precedes_context7(self):
        self.efficiency_section()

    def test_efficiency_section_carries_every_rule(self):
        prose = " ".join(self.efficiency_section().split())
        for phrase in (
            "resends the whole conversation",
            "never the design of the code",
            "60_Operational_Manual/68_Dev_Workflow/codex-build-loop.md",
            "Never wait in a loop.",
            "time limit long enough to finish in one call",
            "one patch per change",
            "Do not run a formatter yourself on Python, Rust or Go files",
            "Unable to format",
            "the repository's own formatting instructions",
            "quiet flags, tail, grep for failures",
            "rg -n",
            "Never cat a whole vault note.",
            "date",
            "70_Research/_lookups",
            "never delete or edit them",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, prose)

    def test_efficiency_section_stays_concise(self):
        self.assertLessEqual(len(self.efficiency_section().splitlines()), 20)

    def test_build_skill_reviews_item_once(self):
        prose = " ".join(BUILD_SKILL.read_text().split())
        self.assertIn(
            "Test and review the item once against its *done when* condition, when it is built, rather than after each step.",
            prose,
        )
        self.assertNotIn("each step against its completion condition", prose)

    def test_build_skill_handoff_excludes_self_review(self):
        text = BUILD_SKILL.read_text()
        prose = " ".join(text.split())
        self.assertNotIn("codex review", text)
        self.assertIn(
            "At handoff, give the branch and its commits when commits were authorized, the repository checks and their real output, and the current session transcript path under `~/.codex/sessions/`.",
            prose,
        )

    def test_build_skill_does_not_duplicate_efficiency_rules(self):
        text = BUILD_SKILL.read_text()
        for phrase in (
            "Never wait in a loop",
            "one patch per change",
            "rg -n",
            "70_Research/_lookups",
        ):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, text)

    def checking_work_section(self):
        text = RULES.read_text()
        match = re.search(
            r"^## 7\. Checking work\n(?P<body>.*?)(?=^## |\Z)",
            text,
            re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(match)
        return match.group("body").strip()

    def test_checking_work_stays_concise(self):
        self.assertLessEqual(len(self.checking_work_section().splitlines()), 20)

    def test_checking_work_carries_decision_17(self):
        prose = " ".join(self.checking_work_section().split()).lower()
        for phrase in (
            "correct comes before fast",
            "slow is smooth, and smooth is fast",
            "searched without filters",
            "summary",
            "unchecked",
            "only the question",
            "slow down further",
            "decision 17",
            "the operating model wins",
            "vault system decision 20",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, prose)

    def test_checking_work_keeps_existing_guards(self):
        prose = " ".join(self.checking_work_section().split())
        for phrase in (
            "Never declare work complete without evidence.",
            "Keep planned and deployed state distinct.",
            "production contact-form tests send real mail and require deliberate authorization.",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, prose)

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
