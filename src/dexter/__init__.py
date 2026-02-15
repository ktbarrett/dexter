from __future__ import annotations

from dexter._decorator import task
from dexter._task import Task

__all__ = [
    "Task",
    "task",
]

for name in __all__:
    globals()[name].__module__ = __name__
