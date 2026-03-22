from __future__ import annotations

from dexter._flow import linearize


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
