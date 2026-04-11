from __future__ import annotations

import subprocess
import sys
from contextlib import chdir
from pathlib import Path

testfiles_dir = Path(__file__).parent / "testfiles"


def test_as_module_main() -> None:
    with chdir(testfiles_dir):
        subprocess.run([sys.executable, "-m", "dexter", "--help"], check=True)


def test_as_script() -> None:
    with chdir(testfiles_dir):
        subprocess.run(["dex", "--help"], check=True)
