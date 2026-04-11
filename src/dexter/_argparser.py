from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from dexter._task import PositionType

if TYPE_CHECKING:
    from dexter._loader import TaskFile


def build_argparser(taskfile: TaskFile) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dex")
    parser.add_argument("--list", action="store_true", help="List all available tasks")
    task_group = parser.add_subparsers(
        title="task", required=True, help="The task to run"
    )
    for task_flow in taskfile.task_flows:
        task_parser = task_group.add_parser(task_flow.name, help=task_flow.description)
        for arg in task_flow.args:
            ...
    return parser
