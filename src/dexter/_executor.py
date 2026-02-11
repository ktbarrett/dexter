from __future__ import annotations

from collections.abc import Hashable, Mapping
from functools import cache
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Sequence


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
