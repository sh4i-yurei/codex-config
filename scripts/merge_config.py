"""Copy the versioned permission settings into a machine's Codex config."""

import os
import re
import shutil
import tempfile
import tomllib
from datetime import datetime
from pathlib import Path

SECTION = re.compile(r"^\s*\[([^]]+)\]\s*(?:#.*)?$")
KEY = re.compile(r"^\s*([A-Za-z_][A-Za-z_0-9]*)\s*=")


def merged_config(base_text: str, profile_text: str) -> str:
    profile = tomllib.loads(profile_text)
    if profile.get("default_permissions") != "mark":
        raise ValueError("mark.config.toml must select the mark permission profile")
    if profile.get("memories") != {"generate_memories": False, "use_memories": False}:
        raise ValueError("mark.config.toml must disable both memory operations")
    tomllib.loads(base_text)

    kept = []
    section = ""
    has_memories = False
    for line in base_text.splitlines(keepends=True):
        match = SECTION.match(line)
        if match:
            section = match.group(1)
            if section == "memories":
                has_memories = True
                kept.append(line)
                kept.append("generate_memories = false\nuse_memories = false\n")
                continue
            if section == "permissions.mark" or section.startswith("permissions.mark."):
                continue
        if section == "permissions.mark" or section.startswith("permissions.mark."):
            continue
        key = KEY.match(line)
        if key and section == "" and key.group(1) == "default_permissions":
            continue
        if key and section == "memories" and key.group(1) in {"generate_memories", "use_memories"}:
            continue
        kept.append(line)

    other = "".join(kept).strip("\n")
    permissions_part = profile_text[profile_text.index("[permissions.mark]"):]
    permission_tables, memory_table = permissions_part.split("[memories]", 1)
    if not has_memories:
        other = f"{other}\n\n[memories]{memory_table.rstrip()}"
    result = f'default_permissions = "mark"\n\n{other}\n\n{permission_tables.rstrip()}\n'
    tomllib.loads(result)
    return result


def install_profile_config(home: Path, profile_path: Path) -> None:
    config = home / ".codex/config.toml"
    if not profile_path.is_file():
        return
    if config.is_symlink():
        raise ValueError(f"Refusing to merge into symlinked config: {config}")
    old = config.read_text() if config.exists() else ""
    profile_text = profile_path.read_text()
    current = tomllib.loads(old)
    desired = tomllib.loads(profile_text)
    if (
        current.get("default_permissions") == "mark"
        and current.get("permissions", {}).get("mark") == desired["permissions"]["mark"]
        and all(current.get("memories", {}).get(key) is value for key, value in desired["memories"].items())
    ):
        print(f"OK: {config} already has the mark defaults")
        return
    new = merged_config(old, profile_text)
    if new == old:
        print(f"OK: {config} already has the mark defaults")
        return
    config.parent.mkdir(parents=True, exist_ok=True)
    if config.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup = config.with_name(f"config.toml.bak-{stamp}")
        shutil.copy2(config, backup)
        print(f"Backup: {backup}")
    mode = config.stat().st_mode if config.exists() else 0o600
    with tempfile.NamedTemporaryFile(mode="w", dir=config.parent, prefix="config.toml.", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(new)
    try:
        os.chmod(temporary, mode & 0o777)
        temporary.replace(config)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Configured: {config} uses the mark permission profile and keeps machine settings")
