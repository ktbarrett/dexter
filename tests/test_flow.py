from __future__ import annotations

from dexter._flow import resolve_tasks
from dexter._task import Any, Sequence, Task


def make_task(
    name: str,
    preds: Sequence[Task[Any, Any] | str],
    succs: Sequence[Task[Any, Any] | str],
) -> Task[[], None]:
    return Task(
        name=name,
        description="",
        args=[],
        predecessors=preds,
        successors=succs,
        body=lambda: None,
    )


def test_resolve_tasks() -> None:
    task_a = make_task("A", [], [])
    task_b = make_task("B", ["A"], [])
    task_c = make_task("C", [task_a, "B"], ["D"])
    task_d = make_task("D", ["B"], [task_c])
    tasks = [task_a, task_b, task_c, task_d]
    resolve_tasks(tasks)
    assert task_a.predecessors == []
    assert task_a.successors == []
    assert task_b.predecessors == [task_a]
    assert task_b.successors == []
    assert task_c.predecessors == [task_a, task_b]
    assert task_c.successors == [task_d]
    assert task_d.predecessors == [task_b]
    assert task_d.successors == [task_c]


def test_resolve_tasks_duplicate_names() -> None:
    task_a1 = make_task("A", [], [])
    task_a2 = make_task("A", [], [])
    tasks = [task_a1, task_a2]
    try:
        resolve_tasks(tasks)
        assert False, "Expected ValueError for duplicate task names"
    except ValueError as e:
        assert str(e) == "Duplicate task name found: A"


def test_resolve_tasks_unknown_pred() -> None:
    task_a = make_task("A", ["X"], [])
    tasks = [task_a]
    try:
        resolve_tasks(tasks)
        assert False, "Expected ValueError for unknown predecessor"
    except ValueError as e:
        assert str(e) == "Task A has predecessor X which is not a known task"


def test_resolve_tasks_unknown_succ() -> None:
    task_a = make_task("A", [], ["Y"])
    tasks = [task_a]
    try:
        resolve_tasks(tasks)
        assert False, "Expected ValueError for unknown successor"
    except ValueError as e:
        assert str(e) == "Task A has successor Y which is not a known task"
