"""Link the available configuration pieces without discarding existing files."""

import argparse
from datetime import datetime
from pathlib import Path

from merge_config import install_profile_config

ROOT = Path(__file__).resolve().parents[1]
LINKS = {
    "global-rules.md": ".codex/AGENTS.md",
    "hooks.json": ".codex/hooks.json",
    "hooks": ".codex/hooks",
    "mark.config.toml": ".codex/mark.config.toml",
    "skills": ".agents/skills",
}


def backup(path):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    target = path.with_name(f"{path.name}.bak-{stamp}")
    path.rename(target)
    print(f"Backup: {target}")


def install(home):
    for source_name, destination_name in LINKS.items():
        source = ROOT / source_name
        destination = home / destination_name
        if not source.exists():
            print(f"Pending: {source_name}; no link created")
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.is_symlink() and destination.resolve() == source.resolve():
            print(f"OK: {destination} -> {source}")
            continue
        if destination.exists() or destination.is_symlink():
            backup(destination)
        destination.symlink_to(source, target_is_directory=source.is_dir())
        print(f"Linked: {destination} -> {source}")
    install_profile_config(home, ROOT / "mark.config.toml")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=Path.home(), help="Target home (also used for isolated tests)")
    args = parser.parse_args()
    install(args.home.expanduser().resolve())


if __name__ == "__main__":
    main()
