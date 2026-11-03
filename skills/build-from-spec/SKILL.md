---
name: build-from-spec
description: Build an approved item from Mark's decided project note, keeping its live buildlog and project status current, then hand off verified work. Use for implementation work tied to a project note; leave research and planning to Claude.
---

# Build from spec

Read the folder's `AGENTS.md` and the project note it names. Identify the next
item being built, its exact *done when* condition and the checks named by the
repository. Read the project's open buildlog and the vault's project and
buildlog READMEs before changing either record. If no buildlog is open, ask
before creating one. If the item depends on an undecided design choice or new
research, name the gap and stop that dependent work for Mark and Claude.

Work on a feature branch. Write buildlog entries during the work, with actual
commands, output and errors. Test and review the item once against its *done when*
condition, when it is built, rather than after each step. Tick the project note's Next item only after the *done when* check
passes; update Where it stands to the current state. Keep vault edits within
the active project's note and buildlog.

At handoff, give the branch and its commits when commits were authorized, the
repository checks and their real output, and the current session transcript path under `~/.codex/sessions/`.
The project note and buildlog should already reflect the verified work.
