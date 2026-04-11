from __future__ import annotations

import importlib.metadata
import sys

from dexter._argparser import parse_args
from dexter._loader import load_task_file


def main() -> None:
    args = parse_args()

    if args.version:
        version = importlib.metadata.version("dexter")
        print(f"dexter v{version}")
        return

    taskfile = load_task_file()

    if args.list_tasks:
        print("Available tasks:")
        for task in taskfile.tasks:
            print(f"- {task.name}")
    elif args.task:
        assert args.task_args is not None
        print(f"Running task {args.task!r} with args: {' '.join(args.task_args)}")
    else:
        print("No task specified. Use --list to see available tasks.")
        sys.exit(1)
