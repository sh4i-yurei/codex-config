# Codex configuration work

Project note: [[Codex setup]]
Buildlog: [[codex-setup-log]]

Build from the project note's Next list and record each step in the open
buildlog. Run `python3 -m unittest discover -s tests -v` and `git diff --check`
from this repository. Run `./setup.sh` when a new linked piece is added,
then check that every installed link resolves to a real source. Confirm hooks
in a fresh Codex session after reviewing and trusting them in `/hooks`.

Read `ARCHITECTURE.md` before changing anything. This checkout is live: setup links it into the
home folder, so build in the worktree the handoff names, never by switching branches here.
