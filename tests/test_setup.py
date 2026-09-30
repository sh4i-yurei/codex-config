"""Exercise the installer against disposable home directories."""

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]
PROFILE_MEMORIES = tomllib.loads((ROOT / "mark.config.toml").read_text())["memories"]


def profile_memories_in(parsed):
    return {key: parsed["memories"][key] for key in PROFILE_MEMORIES}


class SetupTests(unittest.TestCase):
    def test_profile_merge_preserves_machine_state_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config = home / ".codex/config.toml"
            config.parent.mkdir()
            original = (
                'model = "gpt-6-sol"\n[tui]\nscreen_reader_detection_done = true\n'
            )
            config.write_text(original)

            command = [str(ROOT / "setup.sh"), "--home", str(home)]
            first = subprocess.run(command, text=True, capture_output=True, check=True)
            after_first = config.read_text()
            second = subprocess.run(command, text=True, capture_output=True, check=True)

            self.assertIn("Configured:", first.stdout)
            self.assertIn(
                "already has the full-access default and mark profile", second.stdout
            )
            self.assertEqual(after_first, config.read_text())
            self.assertEqual(len(list(config.parent.glob("config.toml.bak-*"))), 1)
            self.assertEqual(
                next(config.parent.glob("config.toml.bak-*")).read_text(), original
            )
            parsed = tomllib.loads(after_first)
            self.assertEqual(parsed["model"], "gpt-6-sol")
            self.assertTrue(parsed["tui"]["screen_reader_detection_done"])
            self.assertEqual(parsed["default_permissions"], ":danger-full-access")
            self.assertEqual(parsed["permissions"]["mark"]["extends"], ":workspace")
            self.assertEqual(parsed["memories"], PROFILE_MEMORIES)
            for name in ("AGENTS.md", "hooks.json", "hooks", "mark.config.toml"):
                self.assertTrue((home / ".codex" / name).is_symlink())

    def test_existing_memories_and_other_permission_profiles_survive(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config = home / ".codex/config.toml"
            config.parent.mkdir()
            config.write_text(
                'default_permissions = ":workspace"\n'
                "[memories]\nuse_memories = false\nmax_unused_days = 45\n"
                '[permissions.other]\nextends = ":read-only"\n'
            )
            command = [str(ROOT / "setup.sh"), "--home", str(home)]
            subprocess.run(command, capture_output=True, text=True, check=True)
            first = config.read_text()
            subprocess.run(command, capture_output=True, text=True, check=True)
            self.assertEqual(first, config.read_text())
            parsed = tomllib.loads(first)
            self.assertEqual(parsed["default_permissions"], ":danger-full-access")
            self.assertEqual(parsed["permissions"]["other"]["extends"], ":read-only")
            self.assertEqual(profile_memories_in(parsed), PROFILE_MEMORIES)
            self.assertEqual(parsed["memories"]["max_unused_days"], 45)

    def test_profile_memory_settings_must_be_true_or_false(self):
        spec = importlib.util.spec_from_file_location(
            "merge_config", ROOT / "scripts/merge_config.py"
        )
        assert spec is not None and spec.loader is not None
        merge_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(merge_config)
        profile = (
            'default_permissions = "mark"\n[permissions.mark]\nextends = ":workspace"\n'
            '[memories]\ngenerate_memories = true\nuse_memories = "yes"\n'
        )
        with self.assertRaises(ValueError):
            merge_config.merged_config("", profile)

    def test_runtime_hook_state_does_not_trigger_rewrite(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            command = [str(ROOT / "setup.sh"), "--home", str(home)]
            subprocess.run(command, capture_output=True, text=True, check=True)
            config = home / ".codex/config.toml"
            config.write_text(
                config.read_text()
                + '\n[hooks.state.example]\ntrusted_hash = "sample"\n'
            )
            before = config.read_text()
            second = subprocess.run(command, capture_output=True, text=True, check=True)
            self.assertEqual(config.read_text(), before)
            self.assertIn(
                "already has the full-access default and mark profile", second.stdout
            )

    def test_inline_and_dotted_machine_settings_merge(self):
        examples = (
            "memories = { use_memories = true, disable_on_external_context = true }\n",
            "memories.use_memories = true\nmemories.disable_on_external_context = true\n",
            '[permissions]\nmark = { extends = ":read-only" }\nother = { extends = ":workspace" }\n',
            'permissions.mark = { extends = ":read-only" }\n',
            'permissions = { mark = { extends = ":read-only" }, other = { extends = ":workspace" } }\n',
            '"default_permissions" = ":workspace"\n[memories]\n"use_memories" = true\n[permissions."mark"]\nextends = ":read-only"\n',
            'permissions = { mark = { extends = ":read-only" }, "my.profile" = { extends = ":workspace" } }\n',
            '[permissions.mark]\nextends = ":read-only"\n[[my_tools]]\nname = "keep"\n',
            'developer_instructions = """\n[memories]\nuse_memories = true\n[permissions.mark]\nkeep this text\n"""\n[permissions.mark]\nextends = ":read-only"\n',
        )
        for original in examples:
            with (
                self.subTest(original=original),
                tempfile.TemporaryDirectory() as directory,
            ):
                home = Path(directory)
                config = home / ".codex/config.toml"
                config.parent.mkdir()
                config.write_text(original)
                command = [str(ROOT / "setup.sh"), "--home", str(home)]
                subprocess.run(command, capture_output=True, text=True, check=True)
                first = config.read_text()
                subprocess.run(command, capture_output=True, text=True, check=True)
                self.assertEqual(first, config.read_text())
                parsed = tomllib.loads(first)
                self.assertEqual(parsed["default_permissions"], ":danger-full-access")
                self.assertEqual(parsed["permissions"]["mark"]["extends"], ":workspace")
                self.assertEqual(profile_memories_in(parsed), PROFILE_MEMORIES)
                if "other" in original:
                    self.assertEqual(
                        parsed["permissions"]["other"]["extends"], ":workspace"
                    )
                if "my.profile" in original:
                    self.assertEqual(
                        parsed["permissions"]["my.profile"]["extends"], ":workspace"
                    )
                if "my_tools" in original:
                    self.assertEqual(parsed["my_tools"], [{"name": "keep"}])
                if "developer_instructions" in original:
                    self.assertEqual(
                        parsed["developer_instructions"],
                        tomllib.loads(original)["developer_instructions"],
                    )


if __name__ == "__main__":
    unittest.main()
