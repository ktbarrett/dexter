from __future__ import annotations

from dexter import task
from dexter._executor import serialize_task_graph


@task
def example() -> None:
    print("This is an example task.")


@task(pre=[example])
def example2() -> None:
    print("This is an example task that depends on the first example task.")


@task(pre=[example, example2])
def example3() -> None:
    print("This is an example task that depends on the first two example tasks.")


serialize_task_graph(example3, [example, example2, example3])
