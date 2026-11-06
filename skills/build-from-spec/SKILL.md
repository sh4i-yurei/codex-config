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
condition, when it is built, rather than after each step. Tick the project
note's Next item only after the *done when* check passes; update Where it
stands to the current state. Keep vault edits within the active project's
note and buildlog.

At handoff, give the branch and its commits when commits were authorized, the
repository checks and their real output, and the current session transcript
path under `~/.codex/sessions/`.
The project note and buildlog should already reflect the verified work.

## Build handoffs

A handoff whose Response has no "Round" line is a build session. A handoff whose
Response ends with "Round <N>: changes required" is a fix session: address only
that round's blocking findings. Follow the handoff's named branch and files.

Write tests first. Each new behaviour test must fail on an assertion about
behaviour before the code exists, never on an import or collection error. A test
of existing behaviour passes from the start and proves itself by killing mutants.
Keep the actual failing assertions in the buildlog.

Run mutation on the functions the item changed, to completion, with at most 10
workers; the default of one per CPU core froze the laptop on 2026-10-28. Follow
the global mutation-evidence and survivor rules.

Commit only after the CI rehearsal the handoff names passes on that commit.
Never push, wait for CI or run a
review. Claude reviews the local commit, pushes and opens the pull request. If a
failure has the same cause as an earlier failure in the item, do not patch it a
second time: record both failures and the cause in the project note's Open
questions, then stop the item.

In the vault, edit only the project note's Open questions, its buildlog and the
handoff's Response; never delete anything in the vault. Put the commit SHA, full
check output, rehearsal output, mutation counts and each survivor with its reason
in that Response. The handoff stays open and the Next item unticked for Claude.
