"""Exercise patch-scoped formatting with a real Python formatter."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "hooks/format_patch.py"


def formatter_env(home, *, fallback=False, rust=False):
    env = {
        "HOME": str(home),
        "PATH": "/usr/bin:/bin" if fallback else os.environ["PATH"],
    }
    if rust:
        for name in ("RUSTUP_HOME", "CARGO_HOME"):
            env[name] = os.environ.get(
                name,
                str(Path.home() / (".rustup" if name == "RUSTUP_HOME" else ".cargo")),
            )
    return env


def install_ruff_fallback(home):
    fallback = home / ".local/bin/ruff"
    fallback.parent.mkdir(parents=True)
    fallback.symlink_to(Path(shutil.which("ruff")).resolve())


class FormatPatchTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ruff"), "ruff is required for this check")
    def test_relative_path_ruff_fallback_formats_named_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            relative_bin = os.path.relpath(
                Path(shutil.which("ruff")).parent, Path.cwd()
            )
            with mock.patch.dict(os.environ, {"PATH": f"{relative_bin}:/usr/bin:/bin"}):
                install_ruff_fallback(root)
            edited = root / "edited.py"
            untouched = root / "untouched.py"
            bad_style = 'value={"a":1}\n'
            edited.write_text(bad_style)
            untouched.write_text(bad_style)
            event = {
                "tool_name": "apply_patch",
                "tool_response": "Exit code: 0\nSuccess. Updated the following files:\nM edited.py\n",
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
                env=formatter_env(root, fallback=True),
            )
            self.assertEqual(result.stdout, "")
            self.assertEqual(edited.read_text(), 'value = {"a": 1}\n')
            self.assertEqual(untouched.read_text(), bad_style)

    @unittest.skipUnless(shutil.which("ruff"), "ruff is required for this check")
    def test_only_existing_patch_path_is_formatted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install_ruff_fallback(root)
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
                env=formatter_env(root, fallback=True),
            )
            self.assertEqual(result.stdout, "")
            self.assertNotEqual(edited.read_text(), bad_style)
            self.assertEqual(untouched.read_text(), bad_style)
            subprocess.run(
                ["ruff", "format", "--check", str(edited)],
                capture_output=True,
                check=True,
                env=formatter_env(root),
            )

    def test_bad_event_exits_cleanly(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(SCRIPT)],
                input="not json",
                text=True,
                capture_output=True,
                check=False,
                env=formatter_env(Path(directory)),
            )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Unable to format patch: JSONDecodeError", result.stdout)

    @unittest.skipUnless(shutil.which("ruff"), "ruff is required for this check")
    def test_named_sibling_file_is_formatted_without_touching_neighbor(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install_ruff_fallback(root)
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
                env=formatter_env(root, fallback=True),
            )
            self.assertEqual(result.stdout, "")
            self.assertEqual(edited.read_text(), 'value = {"a": 1}\n')
            self.assertEqual(untouched.read_text(), bad_style)

    @unittest.skipUnless(shutil.which("ruff"), "ruff is required for this check")
    def test_failed_patch_does_not_format_named_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install_ruff_fallback(root)
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
                env=formatter_env(root, fallback=True),
            )
            self.assertEqual(result.stdout, "")
            self.assertEqual(edited.read_text(), bad_style)

    @unittest.skipUnless(shutil.which("rustfmt"), "rustfmt is required for this check")
    def test_rust_formatter_uses_cargo_edition(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Cargo.toml").write_text(
                '[package]\nname = "example"\nversion = "0.1.0"\nedition = "2021"\n'
            )
            source = root / "src"
            source.mkdir()
            edited = source / "main.rs"
            neighbor = source / "child.rs"
            neighbor_text = 'pub fn hello(){println!("hi");}\n'
            neighbor.write_text(neighbor_text)
            edited.write_text('mod child;\nasync fn main(){println!("hi");}\n')
            event = {
                "tool_name": "apply_patch",
                "tool_response": "Exit code: 0\nSuccess. Updated the following files:\nM main.rs\n",
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
                env=formatter_env(root, rust=True),
            )
            self.assertEqual(result.stdout, "")
            self.assertIn("async fn main() {", edited.read_text())
            self.assertEqual(neighbor.read_text(), neighbor_text)
            subprocess.run(
                [
                    "rustfmt",
                    "--edition",
                    "2021",
                    "--config",
                    "skip_children=true",
                    "--check",
                    str(edited),
                ],
                capture_output=True,
                check=True,
                env=formatter_env(root, rust=True),
            )


if __name__ == "__main__":
    unittest.main()
