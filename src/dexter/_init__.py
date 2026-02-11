from __future__ import annotations

from ._decorator import task
from ._task import Arg, Task

__all__ = ["Arg", "Task", "task"]

# re-export properly
for name in __all__:
    globals()[name].__module__ = __name__
