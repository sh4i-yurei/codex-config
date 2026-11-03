"""Check the orientation hook's event and output contract."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "hooks/session_start.py"


def program_env(home):
    return {"HOME": str(home), "PATH": os.environ["PATH"]}


class SessionStartTests(unittest.TestCase):
    def invoke(self, payload):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(SCRIPT)],
                input=payload,
                text=True,
                capture_output=True,
                check=True,
                env=program_env(Path(directory)),
            )
        hook_output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(hook_output["hookEventName"], "SessionStart")
        return hook_output["additionalContext"]

    def test_repository_orientation_reads_named_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "sample-repo"
            root.mkdir()
            subprocess.run(
                ["git", "init", "-q", str(root)], check=True, env=program_env(root)
            )
            (root / "AGENTS.md").write_text(
                "Project note: [[Sample project]]\nBuildlog: [[sample-log]]\n"
            )
            context = self.invoke(json.dumps({"cwd": str(root), "source": "startup"}))
            lines = context.splitlines()
            self.assertEqual(len(lines), 4)
            self.assertEqual(lines[0], "Repository: sample-repo.")
            self.assertIn("Claude plans and researches", lines[2])
            self.assertEqual(
                lines[3], "Project note: [[Sample project]]. Buildlog: [[sample-log]]."
            )

    def test_missing_input_does_not_fail_session(self):
        context = self.invoke("not json")
        self.assertIn("Orientation unavailable", context)

    def test_nested_instructions_inherit_parent_record_names(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "sample-repo"
            nested = root / "nested"
            nested.mkdir(parents=True)
            subprocess.run(
                ["git", "init", "-q", str(root)], check=True, env=program_env(root)
            )
            (root / "AGENTS.md").write_text(
                "Project note: [[Parent]]\nBuildlog: [[parent-log]]\n"
            )
            (nested / "AGENTS.md").write_text("# Local rules\n")
            context = self.invoke(json.dumps({"cwd": str(nested), "source": "startup"}))
            self.assertIn(
                "Project note: [[Parent]]. Buildlog: [[parent-log]].", context
            )


if __name__ == "__main__":
    unittest.main()
