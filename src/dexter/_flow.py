from __future__ import annotations

from collections.abc import Hashable, Mapping, Sequence
from collections.abc import Collection, Hashable, Mapping
from dataclasses import dataclass
from functools import cache
from typing import Any, TypeVar, cast

from dexter._task import Arg, Task

T = TypeVar("T", bound=Hashable)


def resolve_tasks(tasks: Sequence[Task[Any, Any]]) -> None:
    """Resolve str forward references in task predecessors and successors to actual Task objects.

    This also ensures that task names are unique across the set of tasks.
    """
    names_to_tasks: dict[str, Task[Any, Any]] = {task.name: task for task in tasks}
    for task in tasks:
        if task.name in names_to_tasks:
            raise ValueError(f"Duplicate task name found: {task.name}")
        names_to_tasks[task.name] = task
        task.predecessors = [
            names_to_tasks[name] if isinstance(name, str) else name
            for name in task.predecessors
        ]
        task.successors = [
            names_to_tasks[name] if isinstance(name, str) else name
            for name in task.successors
        ]


def linearize(
    node: T, dep_tree: Mapping[T, Sequence[T]], debug: bool = False
) -> list[T]:
    """Return a linearized ordering of nodes given a dependency tree.

    This implements the C3 algorithm for linearizing an acyclic ordered dependency graph.

    Args:
        node: The node to linearize from.
        dep_tree: A mapping from each node to the sequence of nodes it depends on.
        debug: If True, print debug information about the linearization process.

    Returns:
        A list of nodes in a linearized order consistent with the dependency tree.
    """
    if debug:
        print(f"Linearizing {node} with dep tree {dep_tree}")

    @cache
    def helper(node: T) -> list[T]:
        res = merge(
            merge_set=[
                [node, *dep_tree[node]],
                *(helper(dep) for dep in dep_tree[node]),
            ],
            associativity=[node, *dep_tree[node]],
        )
        if debug:
            print(f"Linearization of {node}: {res}")
        return res

    def merge(merge_set: Sequence[Sequence[T]], associativity: Sequence[T]) -> list[T]:
        # The output linearization
        linearization: list[T] = []
        # Indexes into each linearization in the merge set
        indexes = [0] * len(merge_set)
        # Index into the overall merge set which still have remaining elements (for speed)
        merge_remaining = [i for i, dep_seq in enumerate(merge_set) if dep_seq]
        # Record of issues encountered when candidates are found in the tails of other sequences, for error reporting
        # tuple is (candidate, candidate_assoc_idx, problem_assoc_idx, candidate_idx_in_problem_assoc)
        issues: list[tuple[T, int, int, int]] = []
        if debug:
            print(f"Starting merge of {associativity[0]} with merge set {merge_set}")
        while merge_remaining:
            candidates_checked: set[T] = set()
            for i in merge_remaining:
                # choose the next candidate from the head of the sequence
                seq_i_head_idx = indexes[i]
                candidate = merge_set[i][seq_i_head_idx]
                # skip candidates we've already checked (can happen if the same candidate is at the head of multiple sequences in the merge set)
                if candidate in candidates_checked:
                    if debug:
                        print(
                            f"Skipping candidate {candidate} from {associativity[i]} because it has already been checked"
                        )
                    continue
                candidates_checked.add(candidate)
                if debug:
                    print(f"Considering candidate {candidate} from {associativity[i]}")
                # search for the candidate in the tails of the other sequences in the merge set
                for j in merge_remaining:
                    seq_j_head_idx = indexes[j]
                    try:
                        candidate_idx = merge_set[j].index(
                            candidate, seq_j_head_idx + 1
                        )
                    except ValueError:
                        continue
                    else:
                        if debug:
                            print(
                                f"Candidate {candidate} found in tail of {associativity[j]} at index {candidate_idx}"
                            )
                        # candidate is present in the tail of another sequence, we cannot add it to the linearization yet
                        # record the issue and try the next candidate
                        issues.append((candidate, i, j, candidate_idx))
                        break
                else:
                    if debug:
                        print(
                            f"Candidate {candidate} not found in any tails, adding to linearization"
                        )
                    # candidate not found in any of the tails, we can add it to the linearization
                    linearization.append(candidate)
                    # remove the candidate from the heads of all sequences in the merge set
                    for j in merge_remaining:
                        if merge_set[j][indexes[j]] == candidate:
                            indexes[j] += 1
                    merge_remaining = [
                        j for j in merge_remaining if indexes[j] < len(merge_set[j])
                    ]
                    break
            else:
                # If we run out of candidates, we can't linearize
                node_being_linearized = associativity[0]
                msg_lines = [
                    f"Cannot linearize {node_being_linearized} because of conflicting orderings:"
                ]
                for (
                    candidate,
                    candidate_assoc_idx,
                    problem_assoc_idx,
                    candidate_idx,
                ) in issues:
                    candidate_assoc = associativity[candidate_assoc_idx]
                    problem_assoc = associativity[problem_assoc_idx]
                    problem_assoc_head_idx = indexes[problem_assoc_idx]
                    missing_preds = merge_set[problem_assoc_idx][
                        problem_assoc_head_idx:candidate_idx
                    ]
                    missing_preds_str = ", ".join(str(pred) for pred in missing_preds)
                    msg_lines.append(
                        f"  Candidate {candidate} required by {candidate_assoc} conflicts with requirements of {problem_assoc}: "
                        f"{missing_preds_str} must come before {candidate}"
                    )
                if debug:
                    print("\n".join(msg_lines))
                raise ValueError("\n".join(msg_lines))

        return linearization

    return helper(node)


def build_dep_tree(
    task: Task[Any, Any],
) -> tuple[dict[Task[Any, Any], tuple[Task[Any, Any], ...]], list[Task[Any, Any]]]:
    """Build the dependency tree for a given task to feed into linearize()"""

    dep_tree: dict[Task[Any, Any], tuple[Task[Any, Any], ...]] = {}
    roots: list[Task[Any, Any]] = []

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

    return dep_tree, roots


def flatten_args(tasks_ordered: Sequence[Task[Any, Any]]) -> Collection[Arg[Any]]:
    """Flatten all args in a sequence of tasks into a single collection of args."""
    all_args: dict[str, tuple[Arg[Any], Task[Any, Any]]] = {}
    for task in tasks_ordered:
        for arg in task.args:
            if arg.name in all_args and (existing := all_args[arg.name])[0] != arg:
                existing_arg, existing_arg_task = existing
                if existing_arg.position_type != arg.position_type:
                    raise ValueError(
                        f"Argument {arg.name} for task {task.name} has conflicting position types with argument "
                        f"of the same name from task {existing_arg_task.name}: "
                        f"{existing_arg.position_type} vs {arg.position_type}"
                    )
                elif existing_arg.default != arg.default:
                    raise ValueError(
                        f"Argument {arg.name} for task {task.name} has conflicting default values with argument "
                        f"of the same name from task {existing_arg_task.name}: "
                        f"{existing_arg.default} vs {arg.default}"
                    )
                elif existing_arg.choices != arg.choices:
                    raise ValueError(
                        f"Argument {arg.name} for task {task.name} has conflicting choices with argument "
                        f"of the same name from task {existing_arg_task.name}: "
                        f"{existing_arg.choices} vs {arg.choices}"
                    )
                elif existing_arg.converter != arg.converter:
                    # Not exactly sure how to handle conflicting converters
                    pass

            all_args[arg.name] = (arg, task)
    return [arg for arg, _ in all_args.values()]


@dataclass(kw_only=True)
class TaskFlow:
    name: str
    description: str
    tasks_ordered: Sequence[Task[Any, Any]]
    args: Collection[Arg[Any]]


def build_flow(main_task: Task[Any, Any], tasks: list[Task[Any, Any]]) -> TaskFlow:
    """Builds a flow from the given main task.

    Flows represent a linearized execution order of tasks derived from the dependency
    structure of the tasks starting from the main task; and also a flattened set of
    all arguments required by the tasks in the flow.
    """
    resolve_tasks(tasks)

    dep_tree, roots = build_dep_tree(main_task)

    flow = Task(
        name=task.name,
        body=lambda: None,
        args=[],
        description=task.description,
        # Must reverse the roots to ensure the last succ is the first dep of the flow so it's the last to execute.
        predecessors=tuple(reversed(roots)),
        successors=(),
    )
    dep_tree[flow] =
    tasks_ordered = linearize(flow, dep_tree)

    # collapse all args into a flat list.
    args_combined: list[Arg[Any]] = flatten_args(tasks_ordered)

    return TaskFlow(
        name=main_task.name,
        description=main_task.description,
        tasks_ordered=tasks_ordered,
        args=args_combined,
    )
