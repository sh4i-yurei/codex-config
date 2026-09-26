"""Exercise patch-scoped formatting with a real Python formatter."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "hooks/format_patch.py"


class FormatPatchTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ruff"), "ruff is required for this check")
    def test_only_existing_patch_path_is_formatted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            edited = root / "edited.py"
            untouched = root / "untouched.py"
            bad_style = 'value={"a":1}\n'
            edited.write_text(bad_style)
            untouched.write_text(bad_style)
            event = {
                "hook_event_name": "PostToolUse",
                "tool_name": "apply_patch",
                "tool_response": "Exit code: 0\nSuccess. Updated the following files:\nM edited.py\n",
                "cwd": str(root),
                "tool_input": {
                    "command": f'*** Begin Patch\n*** Update File: {edited}\n@@\n-value=1\n+value={{"a":1}}\n*** End Patch'
                },
            }
            result = subprocess.run(
                [sys.executable, str(SCRIPT)],
                input=json.dumps(event),
                text=True,
                capture_output=True,
                check=True,
                env={**os.environ, "PATH": "/usr/bin:/bin"},
            )
            self.assertEqual(result.stdout, "")
            self.assertNotEqual(edited.read_text(), bad_style)
            self.assertEqual(untouched.read_text(), bad_style)
            subprocess.run(
                ["ruff", "format", "--check", str(edited)],
                capture_output=True,
                check=True,
            )

    def test_bad_event_exits_cleanly(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input="not json",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Unable to format patch: JSONDecodeError", result.stdout)

    @unittest.skipUnless(shutil.which("ruff"), "ruff is required for this check")
    def test_named_sibling_file_is_formatted_without_touching_neighbor(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            edited = root / "edited.py"
            untouched = root / "untouched.py"
            bad_style = 'value={"a":1}\n'
            edited.write_text(bad_style)
            untouched.write_text(bad_style)
            event = {
                "tool_name": "apply_patch",
                "tool_response": "Exit code: 0\nSuccess. Updated the following files:\nM edited.py\n",
                "cwd": str(workspace),
                "tool_input": {
                    "command": f"*** Begin Patch\n*** Update File: {edited}\n*** End Patch"
                },
            }
            result = subprocess.run(
                [sys.executable, str(SCRIPT)],
                input=json.dumps(event),
                text=True,
                capture_output=True,
                check=True,
                env={**os.environ, "PATH": "/usr/bin:/bin"},
            )
            self.assertEqual(result.stdout, "")
            self.assertEqual(edited.read_text(), 'value = {"a": 1}\n')
            self.assertEqual(untouched.read_text(), bad_style)

    @unittest.skipUnless(shutil.which("ruff"), "ruff is required for this check")
    def test_failed_patch_does_not_format_named_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            edited = root / "edited.py"
            bad_style = 'value={"a":1}\n'
            edited.write_text(bad_style)
            event = {
                "tool_name": "apply_patch",
                "tool_response": "Exit code: 1\nFailed to find expected lines\n",
                "cwd": str(root),
                "tool_input": {
                    "command": f"*** Begin Patch\n*** Update File: {edited}\n*** End Patch"
                },
            }
            result = subprocess.run(
                [sys.executable, str(SCRIPT)],
                input=json.dumps(event),
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertEqual(result.stdout, "")
            self.assertEqual(edited.read_text(), bad_style)


if __name__ == "__main__":
    unittest.main()
