from __future__ import annotations

import runpy
from dataclasses import dataclass
from pathlib import Path

from dexter._flow import TaskFlow, build_flow
from dexter._task import Task


@dataclass(kw_only=True)
class TaskFile:
    task_filepath: Path
    task_flows: list[TaskFlow]


def load_task_file() -> TaskFile:
    task_filepath = Path("tasks.py")
    if not task_filepath.is_file():
        raise FileNotFoundError("No tasks.py file in the current directory")

    # Load tasks.py and find all Task instances
    task_mod = runpy.run_path(str(task_filepath))
    tasks = [obj for obj in task_mod.values() if isinstance(obj, Task)]
    task_flows = [build_flow(task) for task in tasks]

    return TaskFile(task_filepath=task_filepath, task_flows=task_flows)
