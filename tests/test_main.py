from __future__ import annotations

import importlib.metadata
import subprocess
import sys
import tempfile
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


def test_no_task_file() -> None:
    with tempfile.TemporaryDirectory() as tmpdirname, chdir(tmpdirname):
        result = subprocess.run(  # noqa: PLW1510
            ["dex", "--list"],
            capture_output=True,
            text=True,
        )
    assert result.returncode != 0
    assert "No tasks.py file in the current directory" in result.stderr


def test_task_execution() -> None:
    with chdir(testfiles_dir):
        result = subprocess.run(
            ["dex", "hello", "--option", "arg1 arg2"],
            check=True,
            capture_output=True,
            text=True,
        )
    assert "Running task 'hello' with args: --option arg1 arg2" in result.stdout


def test_no_task_specified() -> None:
    with chdir(testfiles_dir):
        result = subprocess.run(  # noqa: PLW1510
            ["dex"],
            capture_output=True,
            text=True,
        )
    assert result.returncode != 0
    assert "No task specified. Use --list to see available tasks." in result.stdout
