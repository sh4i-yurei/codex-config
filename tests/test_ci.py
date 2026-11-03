"""Check the public caller workflow contract."""

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_python_ci_caller():
    path = ROOT / ".github/workflows/ci.yml"
    assert path.is_file()
    workflow = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
    assert workflow == {
        "name": "Python checks",
        "on": {"push": {}, "pull_request": {}},
        "permissions": {"contents": "read"},
        "jobs": {
            "python": {
                "uses": "sh4i-yurei/ci-workflows/.github/workflows/python.yml@8d1ea0f42d357f6639eda1ac9359b9b1420d8789",
                "with": {
                    "coverage_floor": "1",
                    "install_command": "python -m pip install ruff==0.16.0 pytest==9.1.1 pytest-cov==7.1.0",
                    "caller_workflow": ".github/workflows/ci.yml",
                    "caller_job": "python",
                },
            }
        },
    }
