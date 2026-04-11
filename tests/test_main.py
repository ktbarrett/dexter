from __future__ import annotations

import importlib.metadata
import subprocess
import sys
from pathlib import Path

from .test_utils import chdir

testfiles_dir = Path(__file__).parent / "testfiles"


def test_as_module_main() -> None:
    with chdir(testfiles_dir):
        subprocess.run([sys.executable, "-m", "dexter", "--help"], check=True)


def test_as_script() -> None:
    with chdir(testfiles_dir):
        subprocess.run(["dex", "--help"], check=True)


def test_list_tasks() -> None:
    with chdir(testfiles_dir):
        result = subprocess.run(
            ["dex", "--list"],
            check=True,
            capture_output=True,
            text=True,
        )
    assert ("Available tasks:\n- hello") in result.stdout


def test_version() -> None:
    result = subprocess.run(
        ["dex", "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    version = importlib.metadata.version("dexter")
    assert f"v{version}" in result.stdout
