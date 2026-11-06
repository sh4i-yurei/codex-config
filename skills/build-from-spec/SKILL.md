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
In a fix session, read that round's review note and fix every blocking finding;
after each fix run its covering tests and record Saw/Cause/Fix. Then run the
full check once, then the rehearsal gate.

Follow the tests-first and existing-behaviour rules in global-rules.md. If tests
need an interface, create the interface first when tests need it so the first
failure is an assertion. Keep the actual failing assertions in the buildlog.
Tests of existing code describe what it does today, with exact values. Any
behaviour that looks wrong goes in the project note's Open questions with evidence;
never change that behaviour during this item.

While building, run only the tests that cover the change. On a build session,
run the full check once before the done-when, then the done-when itself. Keep
their real output. Make live network requests only when the done-when requires one.

Run mutation on the functions the item changed, to completion, with at most 10
workers; the default of one per CPU core froze the laptop on 2026-10-28. Follow
the global mutation-evidence and survivor rules. For mutmut, use
`mutmut run --max-children 10`.

Commit only after the CI rehearsal the handoff names passes on that commit.
In keepbreathing-infra, run each affected driver job with
`python3 -m ci.run_driver <job>` before committing, and record its last line.
Never push, wait for CI or run a review. Claude reviews the local commit, pushes
and opens the pull request. If a
failure has the same cause as an earlier failure in the item, do not patch it a
second time: record both failures and the cause in the project note's Open
questions, then stop the item.

During a build handoff, this section replaces the first section's project-note steps.
Do not tick the Next item or rewrite Where it stands; Claude does both after review.
In the vault, edit only the project note's Open questions, its buildlog and the
handoff's Response; never delete anything in the vault. Never change the project
note's status or move it. Put the commit SHA, full
check output, rehearsal output, mutation counts and each survivor with its reason
in that Response. The handoff stays open and the Next item unticked for Claude.
End the session after writing the Response.
