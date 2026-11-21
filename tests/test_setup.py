"""Exercise the installer against disposable home directories."""

import os
import re
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import tomllib

from scripts import merge_config

ROOT = Path(__file__).resolve().parents[1]
PROFILE_MEMORIES = tomllib.loads((ROOT / "mark.config.toml").read_text())["memories"]
PROFILE_MARK = tomllib.loads((ROOT / "mark.config.toml").read_text())["permissions"][
    "mark"
]


def install(home, profile=ROOT / "mark.config.toml"):
    output = StringIO()
    with redirect_stdout(output):
        result = merge_config.install_profile_config(home, profile)
    return result, output.getvalue()


def configured_line(config):
    return f"Configured: {config} defaults to full access and keeps the mark profile and machine settings\n"


def ok_line(config):
    return f"OK: {config} already has the full-access default and mark profile\n"


def setup_env(home):
    return {"HOME": str(home), "PATH": os.environ["PATH"]}


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
            first = subprocess.run(
                command, text=True, capture_output=True, check=True, env=setup_env(home)
            )
            after_first = config.read_text()
            second = subprocess.run(
                command, text=True, capture_output=True, check=True, env=setup_env(home)
            )

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
            self.assertEqual(
                (home / ".codex/AGENTS.md").resolve(), ROOT / "global-rules.md"
            )

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
            install(home)
            first = config.read_text()
            install(home)
            self.assertEqual(first, config.read_text())
            parsed = tomllib.loads(first)
            self.assertEqual(parsed["default_permissions"], ":danger-full-access")
            self.assertEqual(parsed["permissions"]["other"]["extends"], ":read-only")
            self.assertEqual(profile_memories_in(parsed), PROFILE_MEMORIES)
            self.assertEqual(parsed["memories"]["max_unused_days"], 45)

    def test_profile_memory_settings_must_be_true_or_false(self):
        profile = (
            'default_permissions = "mark"\n[permissions.mark]\nextends = ":workspace"\n'
            '[memories]\ngenerate_memories = true\nuse_memories = "yes"\n'
        )
        with self.assertRaises(ValueError):
            merge_config.merged_config("", profile)

    def test_runtime_hook_state_does_not_trigger_rewrite(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            install(home)
            config = home / ".codex/config.toml"
            config.write_text(
                config.read_text()
                + '\n[hooks.state.example]\ntrusted_hash = "sample"\n'
            )
            before = config.read_text()
            _, second_output = install(home)
            self.assertEqual(config.read_text(), before)
            self.assertEqual(second_output, ok_line(config))

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
                install(home)
                first = config.read_text()
                install(home)
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

    def test_install_into_empty_home(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config = home / ".codex/config.toml"
            result, output = install(home)
            self.assertIsNone(result)
            self.assertEqual(output, configured_line(config))
            self.assertTrue(config.is_file())
            self.assertEqual(config.stat().st_mode & 0o777, 0o600)
            self.assertEqual(list(config.parent.glob("config.toml.bak-*")), [])
            parsed = tomllib.loads(config.read_text())
            self.assertEqual(parsed["default_permissions"], ":danger-full-access")
            self.assertEqual(parsed["permissions"]["mark"], PROFILE_MARK)
            self.assertEqual(parsed["memories"], PROFILE_MEMORIES)

    def test_existing_config_backup_mode_and_repeat(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config = home / ".codex/config.toml"
            config.parent.mkdir()
            original = (
                'model = "gpt-6-sol"\n[tui]\nscreen_reader_detection_done = true\n'
            )
            config.write_text(original)
            config.chmod(0o640)
            _, output = install(home)
            backups = list(config.parent.glob("config.toml.bak-*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(
                output, f"Backup: {backups[0]}\n" + configured_line(config)
            )
            self.assertRegex(
                backups[0].name, r"^config\.toml\.bak-[0-9]{8}-[0-9]{6}-[0-9]{6}$"
            )
            self.assertEqual(backups[0].read_bytes(), original.encode())
            self.assertEqual(config.stat().st_mode & 0o777, 0o640)
            self.assertEqual(set(config.parent.iterdir()), {config, backups[0]})
            parsed = tomllib.loads(config.read_text())
            self.assertEqual(parsed["model"], "gpt-6-sol")
            self.assertTrue(parsed["tui"]["screen_reader_detection_done"])
            before = config.read_bytes()
            _, output = install(home)
            self.assertEqual(output, ok_line(config))
            self.assertEqual(config.read_bytes(), before)
            self.assertEqual(list(config.parent.glob("config.toml.bak-*")), backups)

    def test_absent_profile_does_not_write_config(self):
        for existing in (False, True):
            with (
                self.subTest(existing=existing),
                tempfile.TemporaryDirectory() as directory,
            ):
                home = Path(directory)
                config = home / ".codex/config.toml"
                if existing:
                    config.parent.mkdir()
                    config.write_text('model = "gpt-6-sol"\n')
                    before = config.read_bytes()
                result, output = install(home, home / "absent.toml")
                self.assertIsNone(result)
                self.assertEqual(output, "")
                if existing:
                    self.assertEqual(config.read_bytes(), before)
                else:
                    self.assertFalse(config.exists())

    def test_symlinked_config_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config = home / ".codex/config.toml"
            config.parent.mkdir()
            target = home / "target.toml"
            target.write_text('model = "gpt-6-sol"\n')
            before = target.read_bytes()
            config.symlink_to(target)
            with self.assertRaisesRegex(
                ValueError,
                f"^Refusing to merge into symlinked config: {re.escape(str(config))}$",
            ):
                install(home)
            self.assertTrue(config.is_symlink())
            self.assertEqual(target.read_bytes(), before)

    def test_each_outdated_condition_triggers_rewrite(self):
        changes = (
            (
                'default_permissions = ":danger-full-access"',
                'default_permissions = ":workspace"',
            ),
            ('extends = ":workspace"', 'extends = ":read-only"'),
            ("use_memories = true", "use_memories = false"),
        )
        for current, outdated in changes:
            with (
                self.subTest(outdated=outdated),
                tempfile.TemporaryDirectory() as directory,
            ):
                home = Path(directory)
                config = home / ".codex/config.toml"
                install(home)
                original = config.read_text()
                self.assertIn(current, original)
                config.write_text(original.replace(current, outdated, 1))
                _, output = install(home)
                backups = list(config.parent.glob("config.toml.bak-*"))
                self.assertEqual(len(backups), 1)
                self.assertEqual(
                    output, f"Backup: {backups[0]}\n" + configured_line(config)
                )
                parsed = tomllib.loads(config.read_text())
                self.assertEqual(parsed["default_permissions"], ":danger-full-access")
                self.assertEqual(parsed["permissions"]["mark"], PROFILE_MARK)
                self.assertEqual(profile_memories_in(parsed), PROFILE_MEMORIES)

    def test_install_creates_missing_parent_folders(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "new/home"
            config = home / ".codex/config.toml"
            _, output = install(home)
            self.assertEqual(output, configured_line(config))
            self.assertTrue(config.is_file())

    def test_merge_rejects_invalid_profile(self):
        profile = (ROOT / "mark.config.toml").read_text()
        with self.assertRaisesRegex(
            ValueError, "^mark.config.toml must select the mark permission profile$"
        ):
            merge_config.merged_config(
                "",
                profile.replace(
                    'default_permissions = "mark"',
                    'default_permissions = "workspace"',
                    1,
                ),
            )
        with self.assertRaisesRegex(
            ValueError,
            "^mark.config.toml must set generate_memories and use_memories to true or false$",
        ):
            merge_config.merged_config(
                "", profile.replace("generate_memories = true\n", "", 1)
            )

    def test_merge_empty_base_layout(self):
        profile = (ROOT / "mark.config.toml").read_text()
        result = merge_config.merged_config("", profile)
        permission_tables = profile[profile.index("[permissions.mark]") :].split(
            "[memories]", 1
        )[0]
        self.assertTrue(
            result.startswith('default_permissions = ":danger-full-access"\n\n')
        )
        self.assertTrue(result.endswith(permission_tables.rstrip() + "\n"))
        parsed = tomllib.loads(result)
        self.assertEqual(parsed["memories"], PROFILE_MEMORIES)


if __name__ == "__main__":
    unittest.main()
