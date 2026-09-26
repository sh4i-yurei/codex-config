---
name: estate-access
description: Access Mark's servers or Vaultwarden-backed credentials through the established dev container, shared session, Git helper and SSH jump host. Use for authorized estate work or fact checks; stop on approval or signing prompts.
---

# Estate access

Say whether a command runs on the host or inside `dev`, and in which folder.
Development tools, Node and `bw` live inside the `dev` Distrobox container.
Load the existing Vaultwarden session from `$XDG_RUNTIME_DIR/bw-session` inside
`dev`; if it is missing or invalid, ask Mark to run `vu`. Keep credential
values out of arguments, output, persistent files and the transcript. GitHub
HTTPS authentication uses the existing `bw` credential helper; use the token
appropriate to the authorized operation.

Use the SSH aliases in `~/.ssh/config`. Reach `web` and `mail` only through the
configured control-plane jump host, never directly by private address. Do not
probe key acceptance through attempted logins. For a Tailscale SSH command
sequence, first run a visible `ssh keepbreath0@<host> true` so Mark can approve
any check link. If a connection stalls, stop and ask which Tailscale or
Bitwarden prompt is showing; do not retry or infer a ban or outage. Read facts
with a command scoped to the authorized host and question, without a password.
