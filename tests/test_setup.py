"""Exercise the installer against disposable home directories."""

import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SetupTests(unittest.TestCase):
    def test_profile_merge_preserves_machine_state_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config = home / ".codex/config.toml"
            config.parent.mkdir()
            original = 'model = "gpt-6-sol"\n[tui]\nscreen_reader_detection_done = true\n'
            config.write_text(original)

            command = [str(ROOT / "setup.sh"), "--home", str(home)]
            first = subprocess.run(command, text=True, capture_output=True, check=True)
            after_first = config.read_text()
            second = subprocess.run(command, text=True, capture_output=True, check=True)

            self.assertIn("Configured:", first.stdout)
            self.assertIn("already has the mark defaults", second.stdout)
            self.assertEqual(after_first, config.read_text())
            self.assertEqual(len(list(config.parent.glob("config.toml.bak-*"))), 1)
            self.assertEqual(next(config.parent.glob("config.toml.bak-*")).read_text(), original)
            parsed = tomllib.loads(after_first)
            self.assertEqual(parsed["model"], "gpt-6-sol")
            self.assertTrue(parsed["tui"]["screen_reader_detection_done"])
            self.assertEqual(parsed["default_permissions"], "mark")
            self.assertEqual(parsed["permissions"]["mark"]["extends"], ":workspace")
            self.assertEqual(parsed["memories"], {"generate_memories": False, "use_memories": False})
            for name in ("AGENTS.md", "hooks.json", "hooks", "mark.config.toml"):
                self.assertTrue((home / ".codex" / name).is_symlink())

    def test_existing_memories_and_other_permission_profiles_survive(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config = home / ".codex/config.toml"
            config.parent.mkdir()
            config.write_text(
                'default_permissions = ":workspace"\n'
                '[memories]\nuse_memories = true\ndisable_on_external_context = true\n'
                '[permissions.other]\nextends = ":read-only"\n'
            )
            command = [str(ROOT / "setup.sh"), "--home", str(home)]
            subprocess.run(command, capture_output=True, text=True, check=True)
            first = config.read_text()
            subprocess.run(command, capture_output=True, text=True, check=True)
            self.assertEqual(first, config.read_text())
            parsed = tomllib.loads(first)
            self.assertEqual(parsed["permissions"]["other"]["extends"], ":read-only")
            self.assertTrue(parsed["memories"]["disable_on_external_context"])
            self.assertFalse(parsed["memories"]["use_memories"])
            self.assertFalse(parsed["memories"]["generate_memories"])

    def test_runtime_hook_state_does_not_trigger_rewrite(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            command = [str(ROOT / "setup.sh"), "--home", str(home)]
            subprocess.run(command, capture_output=True, text=True, check=True)
            config = home / ".codex/config.toml"
            config.write_text(config.read_text() + '\n[hooks.state.example]\ntrusted_hash = "sample"\n')
            before = config.read_text()
            second = subprocess.run(command, capture_output=True, text=True, check=True)
            self.assertEqual(config.read_text(), before)
            self.assertIn("already has the mark defaults", second.stdout)


if __name__ == "__main__":
    unittest.main()
