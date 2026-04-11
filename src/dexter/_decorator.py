from __future__ import annotations

import ast
import inspect
from collections.abc import Callable, Sequence
from enum import Enum
from typing import (
    Any,
    Literal,
    Optional,
    ParamSpec,
    TypeVar,
    Union,
    get_type_hints,
    overload,
)

from dexter._task import Arg, PositionType, Task, empty

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
        default = empty if param.default is param.empty else param.default

        if param.name not in annotations:
            converter, choices = (None, None)
        else:
            converter, choices = parse_annotation(
                annotations[param.name], default is None
            )

        position_type = {
            param.KEYWORD_ONLY: PositionType.KEYWORD_ONLY,
            param.POSITIONAL_ONLY: PositionType.POSITIONAL_ONLY,
            param.POSITIONAL_OR_KEYWORD: PositionType.POSITIONAL_OR_KEYWORD,
            param.VAR_KEYWORD: PositionType.VARIABLE_KEYWORD,
            param.VAR_POSITIONAL: PositionType.VARIABLE_POSITIONAL,
        }[param.kind]

        args.append(
            Arg(
                name=param.name,
                default=default,
                converter=converter,
                description=None,
                position_type=position_type,
                choices=choices,
            )
        )

    task_obj = Task[Params, Result](  # type: ignore[call-arg]  # python/mypy#20819
        name=name or func.__name__,
        description=description or (func.__doc__ or "").strip(),
        args=tuple(args),
        predecessors=tuple(pre) if pre else (),
        successors=tuple(post) if post else (),
        body=func,
    )

    return task_obj


union_types = tuple(
    map(
        type,
        {
            int | str,
            Union[int, str],  # noqa: UP007
            Optional[int],  # noqa: UP045
        },
    )
)

literal_type = tuple(map(type, {Literal[1], Literal["a", 1]}))


def literal_eval(s: str) -> Any:
    """Safely evaluate a string as a Python literal."""
    try:
        # If a int, float, or bool literal, this will return the literal value
        val = ast.literal_eval(s)
    except (Exception, SyntaxError):
        # If it's a string, return it as is
        return s
    else:
        if not isinstance(val, (int, float, bool)):
            # If it's not a supported literal type, return the string
            return s
        return val


def parse_annotation(
    annotation: Any, default_is_None: bool
) -> tuple[Callable[[str], Any] | None, tuple[Any, ...] | None]:
    """Parse an annotation to get a converter, choices, and optionality."""

    if isinstance(annotation, union_types):
        args = annotation.__args__  # type: ignore[attr-defined]
        if len(args) == 1:
            # union of one type is just the type
            return parse_annotation(args[0], default_is_None)
        elif len(args) == 2 and type(None) in args:
            if not default_is_None:
                raise ValueError(
                    f"Annotations that accept `None` must be defaulted with it: {annotation}"
                )
            # converter is the non-None type
            non_none_arg = args[0] if args[1] is type(None) else args[1]
            return parse_annotation(non_none_arg, default_is_None)
        else:
            # the only other unions we support are unions of literals, which we interpret as choices
            choices = parse_choices(annotation)
            return literal_eval, choices
    elif isinstance(annotation, literal_type):
        choices = annotation.__args__  # type: ignore[attr-defined]
        return literal_eval, choices
    elif isinstance(annotation, type) and issubclass(annotation, Enum):
        choices = tuple(annotation)
        return lambda s: annotation[s], choices
    elif isinstance(annotation, type):
        return annotation, None
    else:
        raise ValueError(f"Unsupported annotation: {annotation}")


def parse_choices(annotation: Any) -> tuple[Any, ...]:
    """Parse an annotation to get choices."""
    if isinstance(annotation, union_types):
        choices: list[Any] = []
        for arg in annotation.__args__:  # type: ignore[attr-defined]
            choices.extend(parse_choices(arg))
        return tuple(choices)
    elif isinstance(annotation, literal_type):
        return annotation.__args__  # type: ignore[attr-defined]
    else:
        raise TypeError(f"Unsupported annotation for choices: {annotation}")
