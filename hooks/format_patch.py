"""Format existing Python, Rust and Go files named by an apply_patch event."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import tomllib

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
                raw = line[len(marker) :].strip()
                if raw:
                    path = Path(raw)
                    paths.append(path if path.is_absolute() else cwd / path)
                break
    return dict.fromkeys(paths)


def rust_edition(path: Path) -> str:
    """Read a crate's edition, including an inherited workspace edition."""
    workspace_edition = None
    package_edition = None
    found_package = False
    for folder in (path.parent, *path.parents):
        manifest = folder / "Cargo.toml"
        if not manifest.is_file():
            continue
        try:
            with manifest.open("rb") as stream:
                config = tomllib.load(stream)
        except (OSError, tomllib.TOMLDecodeError):
            continue
        workspace_edition = workspace_edition or config.get("workspace", {}).get(
            "package", {}
        ).get("edition")
        if not found_package and "package" in config:
            found_package = True
            package_edition = config["package"].get("edition", "2015")
            if isinstance(package_edition, str):
                return package_edition
    if (
        isinstance(package_edition, dict)
        and package_edition.get("workspace") is True
        and isinstance(workspace_edition, str)
    ):
        return workspace_edition
    return "2015" if found_package else "2021"


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
        arguments = [executable, *formatter[1:]]
        if path.suffix == ".rs":
            arguments.extend(
                (
                    "--edition",
                    rust_edition(path),
                    "--config",
                    "skip_children=true",
                    "--emit",
                    "stdout",
                )
            )
        result = subprocess.run(
            [*arguments, str(path)],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"Unable to format {path}: {type(exc).__name__}")
        return
    if result.returncode:
        detail = (result.stderr or result.stdout).strip().splitlines()
        print(
            f"Unable to format {path}: {detail[0] if detail else f'exit {result.returncode}'}"
        )
    elif path.suffix == ".rs":
        marker = f"{path}:\n\n"
        if not result.stdout.startswith(marker):
            print(f"Unable to format {path}: rustfmt did not return only this file")
            return
        path.write_text(result.stdout[len(marker) :])


def main() -> None:
    try:
        event = json.load(sys.stdin)
        if event.get("tool_name") != "apply_patch":
            return
        response = event.get("tool_response", "")
        if (
            not isinstance(response, str)
            or not response.startswith("Exit code: 0\n")
            or "Success. Updated the following files:" not in response
        ):
            return
        cwd = Path(event.get("cwd") or Path.cwd())
        command = event.get("tool_input", {}).get("command", "")
        for path in patch_paths(command, cwd):
            format_file(path, cwd)
    except Exception as exc:  # noqa: BLE001
        print(f"Unable to format patch: {type(exc).__name__}")


if __name__ == "__main__":
    main()
