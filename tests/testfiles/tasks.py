from __future__ import annotations

import dexter


@dexter.task
def hello(name: str) -> None:
    print(f"Hello, {name}!")
