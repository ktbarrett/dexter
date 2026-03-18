from __future__ import annotations

from argparse import ArgumentParser


def main() -> None:
    argparse = ArgumentParser(prog="dex")
    group = argparse.add_mutually_exclusive_group()
    group.add_argument(
        "-l", "--list", action="store_true", help="List all available commands"
    )
    # group.add_subparser()
    # TODO Build CLI for all tasks
