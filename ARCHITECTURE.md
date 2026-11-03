# Architecture

How the pieces of this repository fit together, and what each one must not do. When a change
doesn't fit this, change this file first, on purpose, in the same commit.

## The shape

This repository is Codex's live configuration. `setup.sh` links its pieces into the home folder,
so whatever is on `main` in this checkout is what every running Codex session loads. That is why
work happens in a worktree under `~/Documents/worktrees/` and reaches `main` as one commit, never
by switching branches here. The machine's base `~/.codex/config.toml` is outside the repository
and is never replaced by a link. Codex's command guard is not here: `hooks.json` runs
`git-guard.py` from `claude-config`, so both agents share one guard.

## The pieces

| Piece | Responsibility | Interface | Fails how | Must not |
|---|---|---|---|---|
| `global-rules.md` | Codex's instructions for every session, linked as `~/.codex/AGENTS.md` | Markdown, loaded whole | — | Hold instructions for one repository; those go in that repository's `AGENTS.md` |
| `hooks.json` | Wire hooks to Codex's events | Codex hook configuration | — | Reimplement the command guard; it calls `claude-config`'s `git-guard.py` |
| `hooks/session_start.py` | Orient a new or resumed session | SessionStart event, additional context with a size limit | Fails quietly | Change files |
| `hooks/format_patch.py` | Format the files a patch touched | PostToolUse event for `apply_patch` | Leaves files unchanged on error | Format files the patch didn't touch |
| `mark.config.toml` | The `mark` permission profile and memory settings | Codex config profile | — | Replace the machine's base config |
| `scripts/setup.py`, `setup.sh` | Link each piece into place, keep dated backups, merge memory settings | Run by hand | Lists missing pieces as pending | Overwrite a file without keeping a backup |
| `scripts/merge_config.py` | Merge settings into the base config | Called by setup | Refuses to write invalid TOML | Remove settings it didn't add |
| `.github/workflows/ci.yml` | Call the pinned shared Python check | Every push and pull request | CI reports a failed check | Hold a copy of the shared checks' logic |
| `pyproject.toml` | Hold the pytest and mutmut settings the shared check reads | Python tool configuration | A check rejects invalid settings | Duplicate the shared checks' logic |
| `skills/` | Codex skills, linked as `~/.agents/skills` | Loaded when a skill applies | Per skill | Duplicate a rule from `global-rules.md` |
| `tests/` | Tests for the hooks and setup | `python3 -m pytest -q -p no:cacheprovider && git diff --check` | — | Touch the real home folder; use `--home` with a temporary folder |

## Rules every piece follows

- **One guard for both agents.** Command rules live in `claude-config/hooks/git-guard.py`. This
  repository only calls it.
- **Setup is repeatable.** Running it twice changes nothing the second time, and it never
  destroys an existing file.
- **Nothing here holds a secret.** Paths under `~/Documents/lockbox/` may be named; values never.
