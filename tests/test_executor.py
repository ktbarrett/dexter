from __future__ import annotations

import pytest

from dexter._executor import linearize


def test_linearize() -> None:
    assert linearize(1, {1: [2, 3], 2: [4], 3: [4], 4: []}) == [1, 2, 3, 4]

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
    ) == ["Z", "F", "G", "H", "D", "A", "B", "C", "E"]

    assert linearize("Z", {"Z": [], "A": ["Z"]}) == ["Z"]

    with pytest.raises(ValueError):
        # B cannot be bother before C as required by A and after C as required by C
        linearize("A", {"A": ["B", "C"], "C": ["B"], "B": []})
