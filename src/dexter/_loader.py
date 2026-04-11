from __future__ import annotations

import runpy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dexter._task import Task


@dataclass(kw_only=True)
class TaskFile:
    task_filepath: Path
    tasks: list[Task[Any, Any]]


def load_task_file() -> TaskFile:
    task_filepath = Path("tasks.py")
    if not task_filepath.is_file():
        raise FileNotFoundError("No tasks.py file in the current directory")

    # Load tasks.py and find all Task instances
    task_mod = runpy.run_path(str(task_filepath))
    tasks = [obj for obj in task_mod.values() if isinstance(obj, Task)]

    return TaskFile(task_filepath=task_filepath, tasks=tasks)
