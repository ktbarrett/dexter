from __future__ import annotations

import subprocess
import sys


def test_as_module_main() -> None:
    subprocess.run([sys.executable, "-m", "dexter"], check=True)


def test_as_script() -> None:
    subprocess.run(["dex"], check=True)
