import functools
import re
import traceback
from typing import Any, Callable, TypeVar
from .validate import validate
from ..colors import warning
from ..versioned_imports import ParamSpec

T = TypeVar("T")
P = ParamSpec("P")
FuncT = Callable[P, T]  # type:ignore


@validate  # type:ignore
def limit_recursion(max_depth: int, return_value: Any = None, quiet: bool = True) -> Callable[[FuncT], FuncT]:
    """decorator to limit recursion of functions

    Args:
        max_depth (int): max recursion depth which is allowed for this function
        return_value (Any, optional): The value to return when the limit is reached. Defaults to None.
            if is None, will return the last a tuple for the last args, kwargs given
        quiet (bool, optional): whether to print a warning message. Defaults to True.
    """

    def deco(func: FuncT) -> FuncT:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            depth = functools.reduce(
                lambda count, line:
                count + 1 if re.search(rf"{func.__name__}\(.*\)$", line)
                else count,
                traceback.format_stack(), 0
            )
            if depth >= max_depth:
                if not quiet:
                    warning(
                        "limit_recursion has limited the number of calls for "
                        f"{func.__module__}.{func.__qualname__} to {max_depth}")
                if return_value:
                    return return_value
                return args, kwargs
            return func(*args, **kwargs)

        return wrapper

    return deco


__all__ = [
    "limit_recursion"
]
