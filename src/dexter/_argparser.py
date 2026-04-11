from __future__ import annotations

import argparse


class DexterArgs(argparse.Namespace):
    list_tasks: bool
    version: bool
    task: str | None
    task_args: list[str] | None


def parse_args(argv: list[str] | None = None) -> DexterArgs:
    # This parses the main command options and the task name, but not the task args
    parser = argparse.ArgumentParser(prog="dex")
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_tasks",
        help="List all available tasks",
    )
    parser.add_argument("--version", action="store_true", help="Show the version")
    parser.add_argument("task", nargs="?", help="The task to run")
    args, unknown_args = parser.parse_known_args(argv, namespace=DexterArgs())
    args.task_args = unknown_args
    return args
