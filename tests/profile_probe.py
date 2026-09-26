"""Check the active Codex command sandbox using disposable write probes."""

from pathlib import Path

HOME = Path.home()
VAULT = HOME / "Documents/Second_Brain"
PROBES = {
    HOME / "Documents/codex-config/.codex-profile-probe": True,
    VAULT / "10_Projects/16_Tooling/.codex-profile-probe": True,
    VAULT / "20_Buildlogs/codex-setup/.codex-profile-probe": True,
    VAULT / ".codex-profile-probe": False,
    VAULT / "00_Inbox/.codex-profile-probe": False,
    VAULT / "70_Research/.codex-profile-probe": False,
}


def main() -> int:
    failures = []
    for path, expected in PROBES.items():
        if path.exists():
            failures.append(f"pre-existing probe path: {path}")
            continue
        try:
            path.write_text("Codex permission probe\n")
        except OSError as exc:
            allowed = False
            detail = f"{type(exc).__name__}: {exc.strerror}"
        else:
            allowed = True
            detail = "write succeeded"
        finally:
            if path.exists():
                path.unlink()
        print(f"{path}: {detail}; expected {'allowed' if expected else 'denied'}")
        if allowed != expected:
            failures.append(str(path))
    if failures:
        print("FAIL: " + ", ".join(failures))
        return 1
    print("PASS: workspace and project records writable; rest of vault read-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
