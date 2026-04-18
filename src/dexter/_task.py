from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum, auto
from functools import update_wrapper
from typing import Any, Generic, ParamSpec, TypeVar


class PositionType(Enum):
    KEYWORD_ONLY = auto()
    POSITIONAL_ONLY = auto()
    POSITIONAL_OR_KEYWORD = auto()
    VARIABLE_POSITIONAL = auto()
    VARIABLE_KEYWORD = auto()


T = TypeVar("T")
Result = TypeVar("Result")
Params = ParamSpec("Params")


class Empty: ...


empty = Empty()


@dataclass(kw_only=True)
class Arg(Generic[T]):
    name: str
    default: T | Empty = empty
    converter: Callable[[str], T] | None = None
    description: str | None = None
    position_type: PositionType
    choices: Sequence[T] | None = None


# Making this a dataclass causes issues with mypy. If we don't define the __name__,
# __qualname__, __doc__, and __module__ attribute annotations, then we can't use those
# attributes on Task objects without mypy complaining. But if we define them, they have
# to be defaulted dataclass.fields, which is weird and slow and unnecessary.
class Task(Generic[Params, Result]):
    name: str
    description: str
    args: Sequence[Arg[Any]]
    predecessors: Sequence[Task[Any, Any] | str]
    successors: Sequence[Task[Any, Any] | str]
    body: Callable[Params, Result]

    __name__: str
    __qualname__: str
    __doc__: str | None
    __module__: str

    def __init__(
        self,
        name: str,
        description: str,
        args: Sequence[Arg[Any]],
        predecessors: Sequence[Task[Any, Any] | str],
        successors: Sequence[Task[Any, Any] | str],
        body: Callable[Params, Result],
    ) -> None:
        self.name = name
        self.description = description
        self.args = args
        self.predecessors = predecessors
        self.successors = successors
        self.body = body
        update_wrapper(self, self.body)

    def __call__(self, *args: Params.args, **kwargs: Params.kwargs) -> Result:
        return self.body(*args, **kwargs)

    def __repr__(self) -> str:
        return f"Task({self.name})"
