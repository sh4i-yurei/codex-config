# codex-config

Personal instructions, hooks, skills and permission settings for Codex on the laptop.
The specification is the Codex setup project note in the private Second Brain vault.

Run `./setup.sh` from this directory on the host or inside the `dev` Distrobox container.
It links each available piece into the shared home directory. Missing pieces are listed
as pending. Existing files and directories are kept beside their replacements as dated
backups. Repeating setup leaves correct links alone.

| Source | Link |
| --- | --- |
| `global-rules.md` | `~/.codex/AGENTS.md` |
| `hooks.json` | `~/.codex/hooks.json` |
| `hooks/` | `~/.codex/hooks/` |
| `mark.config.toml` | `~/.codex/mark.config.toml` |
| `skills/` | `~/.agents/skills` |

The base `~/.codex/config.toml` belongs to the machine and is never replaced by a link.
Setup makes every `codex` run, plain or `codex exec`, use the `mark` permission profile
that setup copies into `~/.codex/config.toml`. It runs commands in a sandbox that writes
only to the workspace and its own `.git`, the temporary folders, `~/.cache`, `~/.npm`,
`~/.ansible/tmp` and the notes vault, and denies staged secrets, sign-in
files, browser data, the other mounts of the home folder and the host bridges. A main
checkout commits as it is. To commit from a git worktree, start Codex there with
`--add-dir "$(git rev-parse --absolute-git-dir)" --add-dir "$(git rev-parse --path-format=absolute --git-common-dir)"`.
Setup also copies the terminal wait ceiling and memory settings in `mark.config.toml` into the base config. Codex's
memory feature itself is switched on once per machine with `codex features enable memories`.
The root `AGENTS.md` holds this repository's instructions. Global instructions live in
`global-rules.md` so repository instructions stay local to this project.

Use `./setup.sh --home /tmp/codex-setup-test` to inspect installation in a disposable
home directory. Development tools and credential helpers run inside `dev`.
