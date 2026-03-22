from __future__ import annotations

from collections.abc import Hashable, Mapping
from dataclasses import dataclass
from functools import cache
from typing import TYPE_CHECKING, Any, TypeVar, cast

if TYPE_CHECKING:
    from collections.abc import Sequence

    from dexter._task import Arg, Task


T = TypeVar("T", bound=Hashable)


def linearize(
    node: T, dep_tree: Mapping[T, Sequence[T]], debug: bool = False
) -> list[T]:
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
            for i in merge_remaining:
                # choose the next candidate from the head of the sequence
                seq_i_head_idx = indexes[i]
                candidate = merge_set[i][seq_i_head_idx]
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
