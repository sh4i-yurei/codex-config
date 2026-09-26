"""Check the orientation hook's event and output contract."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "hooks/session_start.py"


class SessionStartTests(unittest.TestCase):
    def invoke(self, payload):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input=payload,
            text=True,
            capture_output=True,
            check=True,
        )
        hook_output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(hook_output["hookEventName"], "SessionStart")
        return hook_output["additionalContext"]

    def test_repository_orientation_reads_named_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "sample-repo"
            root.mkdir()
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "AGENTS.md").write_text("Project note: [[Sample project]]\nBuildlog: [[sample-log]]\n")
            context = self.invoke(json.dumps({"cwd": str(root), "source": "startup"}))
            lines = context.splitlines()
            self.assertEqual(len(lines), 4)
            self.assertEqual(lines[0], "Repository: sample-repo.")
            self.assertIn("Claude plans and researches", lines[2])
            self.assertEqual(lines[3], "Project note: [[Sample project]]. Buildlog: [[sample-log]].")

    def test_missing_input_does_not_fail_session(self):
        context = self.invoke("not json")
        self.assertIn("Orientation unavailable", context)


if __name__ == "__main__":
    unittest.main()
