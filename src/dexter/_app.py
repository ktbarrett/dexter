from __future__ import annotations

import importlib.metadata

from dexter._argparser import build_argparser
from dexter._execute import run_flow
from dexter._loader import load_task_file


def main() -> None:
    taskfile = load_task_file()
    parser = build_argparser(taskfile)
    args = parser.parse_args()
    if args.version:
        version = importlib.metadata.version("dexter")
        print(f"dexter v{version}")
    elif args.list:
        print("Available tasks:")
        for task_flow in taskfile.task_flows:
            print(f"- {task_flow.name}")
    else:
        task_flow = args.task
        run_flow(task_flow)
