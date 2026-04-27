from __future__ import annotations

import inspect
from collections.abc import Callable, Generator, Sequence
from enum import Enum
from functools import reduce
from typing import (
    Any,
    Literal,
    Optional,
    ParamSpec,
    TypeVar,
    Union,
    cast,
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

        position_type = {
            param.KEYWORD_ONLY: PositionType.KEYWORD_ONLY,
            param.POSITIONAL_ONLY: PositionType.POSITIONAL_ONLY,
            param.POSITIONAL_OR_KEYWORD: PositionType.POSITIONAL_OR_KEYWORD,
            param.VAR_KEYWORD: PositionType.VARIABLE_KEYWORD,
            param.VAR_POSITIONAL: PositionType.VARIABLE_POSITIONAL,
        }[param.kind]

        type_: type[Any]
        choices: Sequence[Any] | None
        if param.name not in annotations:
            type_, choices = (str, None)
        else:
            type_, choices = parse_annotation(annotations[param.name], default is None)

        args.append(
            Arg(
                name=param.name,
                type_=type_,
                default=default,
                factory=None,
                converter=None,
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

literal_type = type(Literal[1])


def flatten_unions(annotation: Any) -> Generator[type[Any], None, None]:
    """Flatten nested unions in an annotation."""
    if isinstance(annotation, union_types):
        for arg in annotation.__args__:  # type: ignore[attr-defined]
            yield from flatten_unions(arg)
    else:
        yield annotation


def combine_literals(types: tuple[type[Any], ...]) -> tuple[type[Any], ...]:
    """Combine multiple Literal types into a single Literal type with all the choices."""
    literals = [t for t in types if isinstance(t, literal_type)]
    if not literals:
        return types
    nonliterals = [t for t in types if not isinstance(t, literal_type)]
    all_literal_args = tuple(t for type_ in literals for t in type_.__args__)  # type: ignore[attr-defined]
    return (
        *nonliterals,
        cast("type[Any]", Literal[all_literal_args]),
    )


def parse_annotation(
    annotation: Any, default_is_None: bool
) -> tuple[type[Any], Sequence[Any] | None]:
    """Parse an annotation to get a type and choices.

    Args:
        annotation: The annotation to parse.
        default_is_None:
            Whether the default value for this argument is None.

            This is used to remove `None` from an optional annotation if the default value is `None`.

    Returns:
        A tuple of (type, choices) from the annotation.
    """

    # Flatten nested unions and optionals into a list of types.
    types = tuple(flatten_unions(annotation))

    # Combine literals in type list.
    types = combine_literals(types)

    if len(types) == 1:
        # Check if it's a Literal or an Enum to get choices.
        type_ = types[0]
        if isinstance(type_, literal_type):
            choices = type_.__args__  # type: ignore[attr-defined]
            return type_, choices
        elif isinstance(type_, type) and issubclass(type_, Enum):
            choices = tuple(type_)
            return type_, choices
        else:
            return type_, None
    elif len(types) == 2 and type(None) in types and default_is_None:
        # Optional type. The default value is None, so we can remove None from the annotation and use the non-None type as the type.
        non_none_arg = types[0] if types[1] is type(None) else types[1]
        return parse_annotation(non_none_arg, False)
    else:
        # A union of something.
        return reduce(lambda a, b: a | b, types), None
