from __future__ import annotations

from collections.abc import Hashable, Mapping
from dataclasses import dataclass
from functools import cache
from typing import TYPE_CHECKING, Any, TypeVar, cast

if TYPE_CHECKING:
    from collections.abc import Sequence

    from dexter._task import Arg, Task


T = TypeVar("T", bound=Hashable)


def linearize(node: T, dep_tree: Mapping[T, Sequence[T]]) -> list[T]:
    @cache
    def helper(node: T) -> list[T]:
        return merge([node], *(helper(dep) for dep in dep_tree[node]), dep_tree[node])

    def merge(*seqs: Sequence[T]) -> list[T]:
        merge: list[T] = []
        merge_remaining = [list(seq) for seq in seqs if seq]
        while merge_remaining:
            for seq in merge_remaining:
                candidate = seq[0]
                if not any(candidate in seq[1:] for seq in merge_remaining):
                    break
            else:
                raise ValueError("Can't linearize graph")
            merge.append(candidate)
            merge_remaining = [
                r
                for seq in merge_remaining
                if (r := (seq[1:] if seq[0] == candidate else seq))
            ]
        return merge

    return helper(node)


@dataclass(kw_only=True)
class TaskFlow:
    tasks_ordered: list[Task[Any, Any]]
    args: list[Arg[Any]]


def build_flow(task: Task[Any, Any]) -> TaskFlow:
    # Build a tree of tasks to their preds. Explore through succs to find all
    # "terminal" tasks and make the flow the pseudo-task top of the boundary succs.

    dep_tree: dict[object, tuple[object, ...]] = {}
    roots: list[object] = []

    def helper(task: Task[Any, Any]) -> None:
        if task in dep_tree:
            return
        elif task in roots:
            roots.remove(task)
        dep_tree[task] = task.predecessors
        for pred in task.predecessors:
            helper(pred)
        if not task.successors:
            roots.append(task)
        else:
            for succ in task.successors:
                helper(succ)

    helper(task)

    flow_top = object()
    # Must reverse the roots to ensure the last succ is the first dep of the flow so it's the last to execute.
    dep_tree[flow_top] = tuple(reversed(roots))

    flow = linearize(flow_top, dep_tree)
    assert flow[0] is flow_top
    flow = flow[1:]

    # collapse all args into a flat list.
    ...  # TODO

    return TaskFlow(tasks_ordered=cast("list[Task[Any, Any]]", flow), args=[])
