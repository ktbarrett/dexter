from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from dexter._flow import linearize
from dexter._task import Arg, Task


def test_linearize() -> None:
    assert linearize(1, {1: [2, 3], 2: [4], 3: [4], 4: []}, debug=True) == [1, 2, 3, 4]

    assert linearize(
        "Z",
        {
            "Z": ["F", "G", "H"],
            "H": ["D", "A"],
            "G": ["D", "B", "E"],
            "F": ["A", "B", "C"],
            "E": [],
            "D": [],
            "C": [],
            "B": [],
            "A": [],
        },
        debug=True,
    ) == ["Z", "F", "G", "H", "D", "A", "B", "C", "E"]

    assert linearize("Z", {"Z": [], "A": ["Z"]}, debug=True) == ["Z"]

    try:
        linearize("A", {"A": ["B", "C"], "C": ["B"], "B": []}, debug=True)
    except ValueError as e:
        assert "C must come before B" in str(e)
        assert "B must come before C" in str(e)
    else:
        assert False, "Expected ValueError"


def def_task(
    name: str,
    args: Sequence[Arg[Any]],
    predecessors: Sequence[Task[Any, Any]] = (),
    successors: Sequence[Task[Any, Any]] = (),
) -> Task:
    return Task(
        name=name,
        description=name,
        args=args,
        body=lambda: None,
        predecessors=predecessors,
        successors=successors,
    )


def test_build_dep_tree() -> None:
    a = def_task("A")
    b = def_task("B")
    c = def_task("C")
    d = def_task("D")

    a.successors = [b, c]
    b.predecessors = [a]
    c.predecessors = [a]
    b.successors = [d]
    c.successors = [d]
    d.predecessors = [b, c]

    dep_tree, roots = build_dep_tree(a)
    assert dep_tree == {
        a: [b, c],
        b: [d],
        c: [d],
        d: [],
    }
    assert set(roots) == {d}
