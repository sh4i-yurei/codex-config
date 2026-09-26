"""Format existing Python, Rust and Go files named by an apply_patch event."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

FORMATTERS = {
    ".py": ("ruff", "format"),
    ".rs": ("rustfmt",),
    ".go": ("gofmt", "-w"),
}
FALLBACKS = {
    "ruff": (".local/bin/ruff",),
    "rustfmt": (".cargo/bin/rustfmt",),
    "gofmt": ("/usr/bin/gofmt",),
}


def find_formatter(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    for candidate in FALLBACKS[name]:
        path = Path(candidate)
        if not path.is_absolute():
            path = Path.home() / path
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
    return None


def patch_paths(command: str, cwd: Path):
    paths = []
    for line in command.splitlines():
        for marker in ("*** Add File: ", "*** Update File: ", "*** Move to: "):
            if line.startswith(marker):
                raw = line[len(marker):].strip()
                if raw:
                    path = Path(raw)
                    paths.append(path if path.is_absolute() else cwd / path)
                break
    return dict.fromkeys(paths)


def format_file(path: Path, cwd: Path) -> None:
    if not path.is_file():
        return
    formatter = FORMATTERS.get(path.suffix)
    if formatter is None:
        return
    if path.is_symlink():
        print(f"Unable to format {path}: path is a symlink")
        return
    executable = find_formatter(formatter[0])
    if executable is None:
        print(f"Unable to format {path}: {formatter[0]} is not installed")
        return
    try:
        result = subprocess.run(
            [executable, *formatter[1:], str(path)],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"Unable to format {path}: {type(exc).__name__}")
        return
    if result.returncode:
        detail = (result.stderr or result.stdout).strip().splitlines()
        print(f"Unable to format {path}: {detail[0] if detail else f'exit {result.returncode}'}")


def main() -> None:
    try:
        event = json.load(sys.stdin)
        if event.get("tool_name") != "apply_patch":
            return
        cwd = Path(event.get("cwd") or Path.cwd())
        command = event.get("tool_input", {}).get("command", "")
        for path in patch_paths(command, cwd):
            format_file(path, cwd)
    except Exception as exc:
        print(f"Unable to format patch: {type(exc).__name__}")


if __name__ == "__main__":
    main()
