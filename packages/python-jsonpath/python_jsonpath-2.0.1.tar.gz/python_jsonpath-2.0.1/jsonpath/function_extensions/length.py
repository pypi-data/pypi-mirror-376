"""The standard `length` function extension."""
from collections.abc import Sized
from typing import Union

from jsonpath.filter import UNDEFINED
from jsonpath.filter import _Undefined
from jsonpath.function_extensions import ExpressionType
from jsonpath.function_extensions import FilterFunction


class Length(FilterFunction):
    """A type-aware implementation of the standard `length` function."""

    arg_types = [ExpressionType.VALUE]
    return_type = ExpressionType.VALUE

    def __call__(self, obj: Sized) -> Union[int, _Undefined]:
        """Return an object's length.

        If the object does not have a length, the special _Nothing_ value is
        returned.
        """
        try:
            return len(obj)
        except TypeError:
            return UNDEFINED
