from __future__ import annotations

from enum import Enum, auto
from typing import Literal, Optional, Union

import pytest

from dexter import task
from dexter._decorator import literal_eval
from dexter._task import PositionType, empty


def test_decorator_is_function_like_wrapper() -> None:
    a = 1

    @task
    def thing() -> str:
        """sample text"""
        nonlocal a
        a = 2
        return "wow"

    assert thing.__name__ == "thing"
    assert thing.__module__ == __name__
    assert thing.__doc__ == "sample text"

    assert a == 1
    assert thing() == "wow"
    assert a == 2


def test_basic_task_attributes() -> None:
    def thing() -> None:
        """stuff"""

    a = task(thing)

    assert len(a.args) == 0
    assert a.name == "thing"
    assert a.body is thing
    assert a.description == "stuff"


def test_decorator_arguments() -> None:
    @task
    def other() -> None:
        "foo"

    @task(name="sample", description="not lol", pre=[other], post=[other])
    def example() -> None:
        "lol"

    assert len(example.args) == 0
    assert example.name == "sample"
    assert example.description == "not lol"
    assert example.predecessors == (other,)
    assert example.successors == (other,)


def test_args_no_types() -> None:
    @task
    def example(a, b, c):
        return a + b + c

    assert len(example.args) == 3
    assert example.args[0].name == "a"
    assert example.args[1].name == "b"
    assert example.args[2].name == "c"

    for i in range(3):
        assert example.args[i].default is empty
        assert example.args[i].converter is None
        assert example.args[i].description is None
        assert example.args[i].position_type == PositionType.POSITIONAL_OR_KEYWORD
        assert example.args[i].choices is None


def test_args_position_type() -> None:
    @task
    def example(a, /, b, *args, c, **kwargs):
        return a + b + c

    assert len(example.args) == 5
    assert example.args[0].name == "a"
    assert example.args[0].position_type == PositionType.POSITIONAL_ONLY
    assert example.args[1].name == "b"
    assert example.args[1].position_type == PositionType.POSITIONAL_OR_KEYWORD
    assert example.args[2].name == "args"
    assert example.args[2].position_type == PositionType.VARIABLE_POSITIONAL
    assert example.args[3].name == "c"
    assert example.args[3].position_type == PositionType.KEYWORD_ONLY
    assert example.args[4].name == "kwargs"
    assert example.args[4].position_type == PositionType.VARIABLE_KEYWORD


class CustomType:
    def __init__(self, value: str) -> None:
        self.value = value


def test_converter() -> None:
    @task
    def example(a: int, b: CustomType) -> None: ...

    assert len(example.args) == 2

    assert example.args[0].name == "a"
    assert example.args[0].default is empty
    assert example.args[0].converter is int

    assert example.args[1].name == "b"
    assert example.args[1].default is empty
    assert example.args[1].converter is CustomType


def test_defaulted_no_type() -> None:
    @task
    def example(a=0): ...

    assert len(example.args) == 1
    assert example.args[0].name == "a"
    assert example.args[0].converter is None
    assert example.args[0].default == 0


def test_defaulted_with_type() -> None:
    @task
    def example(a: int = 0): ...

    assert len(example.args) == 1
    assert example.args[0].name == "a"
    assert example.args[0].converter is int
    assert example.args[0].default == 0


def test_pipe_optional() -> None:
    @task
    def example(a: int | None = None, /): ...

    assert len(example.args) == 1
    assert example.args[0].name == "a"
    assert example.args[0].converter is int
    assert example.args[0].default is None

    # no default
    with pytest.raises(ValueError):

        @task
        def example(a: int | None, /): ...


def test_Union_optional() -> None:
    @task
    def example(
        a: Union[int, None] = None,  # noqa: UP007
        /,
    ): ...

    assert len(example.args) == 1
    assert example.args[0].name == "a"
    assert example.args[0].converter is int
    assert example.args[0].default is None

    with pytest.raises(ValueError):

        @task
        def example(
            a: Union[int, None],  # noqa: UP007
            /,
        ): ...


def test_Optional_optional() -> None:
    @task
    def example(
        a: Optional[int] = None,  # noqa: UP045
        /,
    ): ...

    assert len(example.args) == 1
    assert example.args[0].name == "a"
    assert example.args[0].converter is int
    assert example.args[0].default is None

    with pytest.raises(ValueError):

        @task
        def example(
            a: Optional[int],  # noqa: UP045
            /,
        ): ...


def test_default_not_None() -> None:
    with pytest.raises(ValueError):

        @task
        def example(a: int | None = 0, /): ...


def test_choices() -> None:
    @task
    def example(a: Literal[1, 2, 3]): ...

    assert len(example.args) == 1
    assert example.args[0].name == "a"
    assert example.args[0].choices == (1, 2, 3)


def test_pipe_choices() -> None:
    @task
    def example(a: Literal["a"] | Literal["b"]): ...

    assert len(example.args) == 1
    assert example.args[0].name == "a"
    assert example.args[0].choices == ("a", "b")


def test_Union_choices() -> None:
    @task
    def example(
        a: Union[Literal["a"], Literal["b"]],  # noqa: UP007
    ): ...

    assert len(example.args) == 1
    assert example.args[0].name == "a"
    assert example.args[0].choices == ("a", "b")


def test_Optional_choices() -> None:
    @task
    def example(
        a: Optional[Literal["a"]] = None,  # noqa: UP045
    ): ...

    assert len(example.args) == 1
    assert example.args[0].name == "a"
    assert example.args[0].converter is not None
    assert example.args[0].converter("a") == "a"
    assert example.args[0].choices == ("a",)


class Color(Enum):
    RED = auto()
    GREEN = auto()
    BLUE = auto()


def test_enum_choices() -> None:
    @task
    def example(a: Color): ...

    assert len(example.args) == 1
    assert example.args[0].name == "a"
    assert example.args[0].converter is not None
    assert example.args[0].converter("RED") == Color.RED
    assert example.args[0].choices == (Color.RED, Color.GREEN, Color.BLUE)


def test_literal_eval() -> None:
    assert literal_eval("123") == 123
    assert literal_eval("1.23") == 1.23
    assert literal_eval("True") is True
    assert literal_eval("False") is False
    assert literal_eval("abc") == "abc"
    assert literal_eval("wow there are spaces") == "wow there are spaces"
    assert (
        literal_eval("this_look_a_lot_like_a_variable_name")
        == "this_look_a_lot_like_a_variable_name"
    )
    assert literal_eval("[1, 2, 3]") == "[1, 2, 3]"
