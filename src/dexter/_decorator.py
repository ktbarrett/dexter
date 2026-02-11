from __future__ import annotations

import ast
import inspect
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Literal,
    Optional,
    ParamSpec,
    TypeVar,
    Union,
    get_type_hints,
    overload,
)

from dexter._task import Arg, PositionType, Task

if TYPE_CHECKING:
    from collections.abc import Sequence

F = TypeVar("F", bound=Callable[..., Any])


Result = TypeVar("Result")
Params = ParamSpec("Params")


@overload
def task(func: Callable[Params, Result]) -> Task[Params, Result]: ...


@overload
def task(
    *,
    name: str | None = None,
    description: str | None = None,
    pre: Sequence[Task[Any, Any]] | None = None,
    post: Sequence[Task[Any, Any]] | None = None,
) -> Callable[[Callable[Params, Result]], Task[Params, Result]]: ...


def task(
    func: F | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    pre: Sequence[Task[Any, Any]] | None = None,
    post: Sequence[Task[Any, Any]] | None = None,
) -> Task[Params, Result] | Callable[[Callable[Params, Result]], Task[Params, Result]]:
    """Mark a function as a task."""
    if func is None:

        def wrapper(f: Callable[Params, Result]) -> Task[Params, Result]:
            return task(  # type: ignore[call-overload]  # we don't want the overload we need to be public
                f,
                name=name,
                description=description,
                pre=pre,
                post=post,
            )

        return wrapper

    signature = inspect.signature(func)
    annotations = get_type_hints(func)

    args: list[Arg[Any]] = []
    for param in signature.parameters.values():
        converter, choices, optional = parse_annotation(annotations[param.name])

        default = None if param.default is param.empty else param.default

        if param.kind == param.KEYWORD_ONLY:
            position_type = PositionType.KEYWORD_ONLY
        elif param.kind == param.POSITIONAL_ONLY:
            position_type = PositionType.POSITIONAL_ONLY
        else:
            position_type = PositionType.POSITIONAL_OR_KEYWORD

        args.append(
            Arg(
                name=param.name,
                default=default,
                converter=converter,
                description=None,
                position_type=position_type,
                optional=optional,
                choices=choices,
            )
        )

    task_obj = Task[Params, Result](
        name=name or func.__name__,
        description=description or (func.__doc__ or "").strip(),
        args=tuple(args),
        predecessors=tuple(pre) if pre else (),
        successors=tuple(post) if post else (),
        body=func,
    )

    return task_obj


union_types = tuple(map(type, {int | str, Union[int, str], Optional[int]}))

literal_type = tuple(map(type, {Literal[1], Literal["a", 1]}))


def parse_annotation(
    annotation: Any,
) -> tuple[Callable[[str], Any] | None, tuple[Any, ...] | None, bool]:
    """Parse an annotation to get a converter, choices, and optionality."""

    if isinstance(annotation, union_types):
        args = annotation.__args__  # type: ignore[attr-defined]
        if len(args) == 1:
            # union of one type is just the type
            return parse_annotation(args[0])
        elif len(args) == 2 and type(None) in args:
            # it's an optional
            non_none_arg = args[0] if args[1] is type(None) else args[1]
            converter, choices, _ = parse_annotation(non_none_arg)
            return converter, choices, True
        else:
            # the only other unions we support are unions of literals, which we interpret as choices
            choices = parse_choices(annotation)
            return ast.literal_eval, choices, False
    elif isinstance(annotation, literal_type):
        choices = annotation.__args__  # type: ignore[attr-defined]
        return ast.literal_eval, choices, False
    elif isinstance(annotation, type) and issubclass(annotation, Enum):
        choices = tuple(annotation)
        return lambda s: annotation[s], choices, False
    elif isinstance(annotation, type):
        return annotation, None, False
    else:
        raise ValueError(f"Unsupported annotation: {annotation}")


def parse_choices(annotation: Any) -> tuple[Any, ...]:
    """Parse an annotation to get choices."""
    breakpoint()
    if isinstance(annotation, union_types):
        choices: list[Any] = []
        for arg in annotation.__args__:  # type: ignore[attr-defined]
            choices.extend(parse_choices(arg))
        return tuple(choices)
    elif isinstance(annotation, literal_type):
        return annotation.__args__  # type: ignore[attr-defined]
    else:
        raise TypeError(f"Unsupported annotation for choices: {annotation}")
