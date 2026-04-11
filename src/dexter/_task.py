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


@dataclass(kw_only=True, unsafe_hash=True)
class Arg(Generic[T]):
    name: str
    default: T | Empty = empty
    converter: Callable[[str], T] | None = None
    description: str | None = None
    position_type: PositionType
    choices: Sequence[T] | None = None


@dataclass(kw_only=True, unsafe_hash=True)
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

    def __post_init__(self) -> None:
        update_wrapper(self, self.body)

    def __call__(self, *args: Params.args, **kwargs: Params.kwargs) -> Result:
        return self.body(*args, **kwargs)

    def __repr__(self) -> str:
        return f"Task({self.name})"
